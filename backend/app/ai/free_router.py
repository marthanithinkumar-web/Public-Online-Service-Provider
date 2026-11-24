"""Route public, fixed FAQ prompts only. Customer and admin input stays on POSP."""
from collections import Counter, deque
from datetime import datetime, timezone
from threading import Lock
from time import monotonic
import os

from .free_transport import FreeTransport, KEYS

_lock = Lock()
_cache = {}
_inflight = set()
_cooldown = {}
_counts = Counter()
_events = deque(maxlen=32)
_day = None
_ORDER = ('groq', 'gemini', 'cloudflare', 'openrouter')
_TOPICS = {
    'help': 'Explain that POSP helps with applications and that users can contact the service team.',
    'privacy': 'Explain that users should never share passwords, OTPs or card numbers in support chat.',
}
_QUESTIONS = {
    'what is posp': ('help', 'English'), 'posp क्या है': ('help', 'Hindi'),
    'posp అంటే ఏమిటి': ('help', 'Telugu'),
    'what should i avoid sharing': ('privacy', 'English'),
}
_LOCAL = {
    ('help', 'English'): 'POSP helps you apply for services. The service team can help with your request.',
    ('help', 'Hindi'): 'POSP सेवाओं के लिए आवेदन करने में सहायता करता है। सेवा टीम आपकी मदद कर सकती है।',
    ('help', 'Telugu'): 'సేవలకు దరఖాస్తు చేసుకోవడానికి POSP సహాయం చేస్తుంది. సేవా బృందాన్ని సంప్రదించవచ్చు.',
    ('privacy', 'English'): 'Keep passwords, OTPs, and card numbers out of support chat.',
}


def _roll_day():
    global _day
    today = datetime.now(timezone.utc).date()
    if _day != today:
        _counts.clear()
        _day = today


def public_faq(question, role):
    key = _QUESTIONS.get(question.strip().rstrip('?.।').casefold())
    if key is None or role not in ('client', 'admin'):
        return None
    cache_key = (role, *key)
    with _lock:
        _roll_day()
        cached = _cache.get(cache_key)
        if cached and cached[0] > monotonic():
            _counts['cache_hits'] += 1
            return cached[1]
        if cache_key in _inflight:
            return _LOCAL[key]
        _inflight.add(cache_key)
    try:
        order = os.getenv(f'POSP_{role.upper()}_AI_PRIORITY', ','.join(_ORDER)).split(',')
        for name in dict.fromkeys(item.strip() for item in order):
            if name not in KEYS:
                continue
            adapter = FreeTransport(name)
            if not adapter.eligible():
                continue
            with _lock:
                _roll_day()
                if _cooldown.get(name, 0) > monotonic() or _counts[name] >= 25:
                    continue
                _counts[name] += 1
            start = monotonic()
            try:
                result = adapter.synthetic_reply(role, f'{_TOPICS[key[0]]} Reply in {key[1]}, in one sentence.')
                if not result or not isinstance(result, str):
                    raise ValueError('Empty answer')
            except Exception:
                with _lock:
                    _counts[name + '_failures'] += 1
                    _cooldown[name] = monotonic() + 120
                    _events.append({'provider': name, 'result': 'fallback'})
                continue
            with _lock:
                _cache[cache_key] = (monotonic() + 300, result)
                _events.append({'provider': name, 'result': 'ok', 'latency_ms': round((monotonic() - start) * 1000)})
            return result
        return _LOCAL[key]
    finally:
        with _lock:
            _inflight.discard(cache_key)


def routing_status():
    with _lock:
        _roll_day()
        return {'scope': 'current process, UTC day', 'counts': dict(_counts), 'events': list(_events),
                'providers': {name: {'eligible': FreeTransport(name).eligible(),
                                     'cooling_down': _cooldown.get(name, 0) > monotonic()} for name in _ORDER}}
