"""Instance-local AI settings and daily reservations shared by server workers."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile

from .free_transport import KEYS
from .providers.errors import ProviderError


PROVIDERS = ('groq', 'gemini', 'cloudflare', 'openrouter')
ROLES = ('client', 'admin')


def _directory():
    default = Path(tempfile.gettempdir()) / f'posp-free-ai-{getattr(os, "getuid", lambda: 0)()}'
    path = Path(os.environ.get('POSP_AI_STATE_DIR') or default)
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.is_symlink() or (os.name == 'posix' and (path.stat().st_uid != os.getuid() or path.stat().st_mode & 0o077)):
        raise OSError('Invalid state directory permissions')
    return path


def _valid_order(order):
    return isinstance(order, list) and len(order) <= len(KEYS) and all(
        isinstance(name, str) and name in KEYS for name in order) and len(set(order)) == len(order)


def _defaults(role):
    names = os.getenv(f'POSP_{role.upper()}_AI_PRIORITY', ','.join(PROVIDERS)).split(',')
    return list(dict.fromkeys(name.strip() for name in names if name.strip() in KEYS))


@contextmanager
def _state(write=False):
    try:
        directory = _directory()
        with (directory / 'routing.lock').open('a+b') as lock:
            if os.name == 'nt':
                import msvcrt
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
            else:
                import fcntl
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            path = directory / 'routing.json'
            try:
                data = json.loads(path.read_text(encoding='utf-8'))
            except FileNotFoundError:
                data = {'orders': {}, 'day': '', 'attempts': {}}
            orders = data['orders']
            counts = data['attempts']
            if not isinstance(orders, dict) or not all(role in ROLES and _valid_order(order) for role, order in orders.items()):
                raise ValueError('Invalid settings')
            if not isinstance(counts, dict) or not all(k in KEYS and type(v) is int and v >= 0 for k, v in counts.items()):
                raise ValueError('Invalid counts')
            today = datetime.now(timezone.utc).date().isoformat()
            if data['day'] != today:
                data.update(day=today, attempts={})
            yield data
            if write:
                with tempfile.NamedTemporaryFile('w', dir=directory, delete=False, encoding='utf-8') as tmp:
                    name = tmp.name
                    try:
                        json.dump(data, tmp)
                        tmp.flush()
                        os.fsync(tmp.fileno())
                    except BaseException:
                        tmp.close()
                        os.unlink(name)
                        raise
                try:
                    os.replace(name, path)
                finally:
                    Path(name).unlink(missing_ok=True)
    except (OSError, ValueError, KeyError, TypeError):
        raise ProviderError('unavailable', 'Shared free-provider settings are unavailable.') from None


def snapshot():
    with _state() as data:
        return {'orders': {role: data['orders'].get(role, _defaults(role)) for role in ROLES},
                'attempts': dict(data['attempts'])}


def set_order(role, order):
    if role not in ROLES or not _valid_order(order):
        raise ValueError('Choose each supported provider at most once.')
    with _state(write=True) as data:
        data['orders'][role] = list(order)


def reserve(name, role, limit):
    with _state(write=True) as data:
        if name not in data['orders'].get(role, _defaults(role)):
            raise ProviderError('disabled', 'Provider is disabled for this role.')
        used = data['attempts'].get(name, 0)
        if used >= limit:
            raise ProviderError('rate_limited', 'The instance daily allowance is exhausted.')
        data['attempts'][name] = used + 1
