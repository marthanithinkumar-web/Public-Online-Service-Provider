"""Route public, fixed FAQ prompts only. Customer and admin input stays on POSP."""
from collections import Counter, deque
from datetime import datetime, timezone
from threading import Lock
from time import monotonic
import os

from .free_transport import FreeTransport, KEYS
from .providers.errors import ProviderError

_lock = Lock()
_cache = {}
_inflight = set()
_cooldown = {}
_counts = Counter()
_events = deque(maxlen=32)
_day = None
_DAILY_LIMIT = 25
_ORDER = ('groq', 'gemini', 'cloudflare', 'openrouter')
_TOPICS = {
    'help': 'Explain that POSP helps with applications and that users can contact the service team.',
    'privacy': 'Explain that users should never share passwords, OTPs or card numbers in support chat.',
}
_QUESTIONS = {
    'what is posp': ('help', 'English'), 'posp क्या है': ('help', 'Hindi'),
    'posp అంటే ఏమిటి': ('help', 'Telugu'),
    'मुझे चैट में क्या साझा नहीं करना चाहिए': ('privacy', 'Hindi'),
    'చాట్‌లో ఏమి పంచుకోకూడదు': ('privacy', 'Telugu'),
    'what should i avoid sharing': ('privacy', 'English'),
}
_LOCAL = {
    ('help', 'English'): 'POSP helps you apply for services. The service team can help with your request.',
    ('help', 'Hindi'): 'POSP सेवाओं के लिए आवेदन करने में सहायता करता है। सेवा टीम आपकी मदद कर सकती है।',
    ('help', 'Telugu'): 'సేవలకు దరఖాస్తు చేసుకోవడానికి POSP సహాయం చేస్తుంది. సేవా బృందాన్ని సంప్రదించవచ్చు.',
    ('privacy', 'Hindi'): 'चैट में पासवर्ड, ओटीपी या कार्ड नंबर साझा न करें।',
    ('privacy', 'Telugu'): 'చాట్‌లో పాస్‌వర్డ్‌లు, ఓటీపీలు లేదా కార్డు నంబర్లు పంచుకోకండి.',
    ('privacy', 'English'): 'Keep passwords, OTPs, and card numbers out of support chat.',
}


def _roll_day():
    global _day
    today = datetime.now(timezone.utc).date()
    if _day != today:
        _counts.clear()
        _day = today


def _request(name, role, prompt):
    adapter = FreeTransport(name)
    if not adapter.eligible():
        raise ProviderError('disabled', 'Free-tier account is unverified.')
    with _lock:
        _roll_day()
        if _cooldown.get(name, 0) > monotonic() or _counts[name] >= _DAILY_LIMIT:
            raise ProviderError('rate_limited', 'Free-provider request budget or cooldown is active.')
        _counts[name] += 1
        reserved_day = _day
    start = monotonic()
    try:
        result = adapter.synthetic_reply(role, prompt)
        if not isinstance(result, str) or not result.strip():
            raise ValueError('Empty provider response')
    except Exception as exc:
        with _lock:
            _counts[name + '_failures'] += 1
            _cooldown[name] = monotonic() + 120
            _events.append({'provider': name, 'result': 'fallback'})
        if isinstance(exc, ProviderError):
            raise
        raise ProviderError('unavailable', 'Free provider is unavailable.') from None
    finally:
        with _lock:
            _roll_day()
            if _day == reserved_day:
                if adapter.reported_tokens is None:
                    _counts[name + '_missing_usage'] += 1
                else:
                    _counts[name + '_tokens'] += adapter.reported_tokens
    with _lock:
        _events.append({'provider': name, 'result': 'ok', 'latency_ms': round((monotonic() - start) * 1000)})
    return result


def benchmark_reply(name, role, language):
    if name not in KEYS or role not in ('client', 'admin') or language not in ('English', 'Hindi', 'Telugu'):
        raise ProviderError('disabled', 'Unknown evaluation configuration.')
    return _request(name, role, f'Explain in {language} that the fixture assistance fee is 73 INR.')


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
            try:
                result = _request(name, role, f'{_TOPICS[key[0]]} Reply in {key[1]}, in one sentence.')
            except ProviderError:
                continue
            with _lock:
                _cache[cache_key] = (monotonic() + 300, result)
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
                                     'remaining_requests': max(0, _DAILY_LIMIT - _counts[name]),
                                     'failures': _counts[name + '_failures'],
                                     'reported_tokens': _counts[name + '_tokens'],
                                     'attempts_without_usage': _counts[name + '_missing_usage'],
                                     'cooling_down': _cooldown.get(name, 0) > monotonic()} for name in _ORDER}}
