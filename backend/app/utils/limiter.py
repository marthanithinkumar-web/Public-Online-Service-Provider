import os

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


DEFAULT_RATE_LIMITS = ('2000 per day', '500 per hour')
FALLBACK_MAX_SECONDS = 300

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=DEFAULT_RATE_LIMITS,
    storage_uri=os.getenv('RATELIMIT_STORAGE_URI', 'memory://'),
    in_memory_fallback_enabled=True,
)


def storage_degraded() -> bool:
    """Return whether Flask-Limiter 2.9.0 is using its process-local fallback."""
    return bool(limiter._storage_dead)
