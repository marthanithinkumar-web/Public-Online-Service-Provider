# POSP Distributed Rate-Limiting Security Report

## Status

Implementation and local backend verification are complete. The Redis-backed
cross-worker CI test, merge/push, and post-deployment checks are pending. Do
not treat production activation as verified until those checks finish.

## Root cause

The application assigned `limiter._default_limits` after constructing
Flask-Limiter 2.9.0. That private assignment did not register any default
limit groups, leaving ordinary unannotated routes without the intended global
quotas. The pinned constructor API accepts `default_limits`, so the defaults
now register at limiter construction.

## Implementation

- Global defaults are **500 requests per hour** and **2,000 requests per day**.
- Existing route-specific authentication and password-reset limits remain
  unchanged.
- The backend continues to use `RATELIMIT_STORAGE_URI`; it does not substitute
  `REDIS_URL`. The existing key function remains Flask-Limiter's
  `get_remote_address`; no client-supplied forwarding header is parsed directly.
- `/health` and `/readiness` are exempt from rate-limit quotas.
- `/health` is a liveness-only response. `/readiness` checks the database,
  configuration, and dependency connectivity without returning credentials or
  connection strings.
- The Render blueprint sets `STRICT_PRODUCTION_READINESS=1`, so any required
  dependency failure returns HTTP 503 from `/readiness`.

## Redis/Valkey outage policy

When a configured shared store fails, Flask-Limiter logs the failure and
switches ordinary rate-limited routes to its per-process memory store. That
fallback preserves configured limits locally but is **not distributed**.
Production authentication-blueprint requests fail closed with HTTP 503 while
shared storage is unavailable. Other rate-limited routes can use the local
fallback for at most five minutes after the worker detects the outage; after
that, they also fail closed. `/health` remains available for liveness, while
strict `/readiness` reports the dependency failure. Recovery detection returns
the limiter to shared storage, after which counters are shared again.

The policy applies the same controls when production shared storage is absent
or misconfigured at startup. It does not expose the Redis URL or credentials
in logs or responses.

## Redis and production evidence

- The pinned backend dependency is `Flask-Limiter==2.9.0`.
- Render's project dashboard shows the existing
  `public-online-service-provider-rate-limit` Key Value service running Valkey
  8.1.4. No replacement instance was created.
- Before this remediation was deployed, production `/readiness` returned
  HTTP 200 with all ten checks true, including
  `shared_rate_limit_connectivity=true`. This endpoint PINGs the configured
  `RATELIMIT_STORAGE_URI`; it does not reveal the URI.
- The exact secret URL was not copied into this report. An exact hostname
  comparison between the service's masked environment variable and the
  dashboard resource is not independently recorded.
- CI now provisions Redis 7 and tests that independent limiter instances
  (simulating workers) share counters and use separate remote-address keys.
  That CI result is pending.
- Production quota thresholds were not probed with repeated requests, to avoid
  locking out legitimate users or creating load.

## Tests and checks

| Check | Result |
|---|---|
| Full backend suite | **334 passed, 1 skipped, 129 warnings** in 135.88s |
| Focused limiter/readiness/auth/basic tests | **55 passed, 9 warnings** in 18.58s |
| Global hourly default | 500 unannotated-route requests pass; request 501 receives HTTP 429 |
| Global daily default | 2,000 unannotated-route requests pass; request 2,001 receives HTTP 429 |
| Auth route limits | Login, registration, password-reset request, and password-reset limits pass |
| Health/readiness exemptions | More than 500 repeated requests to each remain unthrottled |
| Redis outage fallback | Local fallback enforces route limits and logs the transition |
| Auth outage behavior | Production auth fails closed on a storage failure or missing shared-storage configuration |
| Bounded fallback | Non-auth rate-limited requests fail closed after the five-minute window |
| Redis recovery | Limiter resumes using the shared backend after the simulated reconnect |
| Readiness PING failure | Readiness reports failure without returning connection details |
| Redis cross-worker integration | Added to CI; skipped locally because no Redis server is installed |
| Backend compilation | Passed |
| `git diff --check` | Passed |
| Lint/format | No Python linter or formatter is configured in the repository |

The full suite's one skip is the environment-dependent Redis integration test,
not a failing test. CI is configured to run it against its Redis service.

## Files changed

- `.github/workflows/ci.yml`
- `backend/.env.production.example`
- `backend/app/main.py`
- `backend/app/utils/limiter.py`
- `backend/tests/test_basic.py`
- `backend/tests/test_rate_limits.py`
- `backend/tests/test_rate_limits_redis_integration.py`
- `backend/tests/test_readiness.py`
- `POSP_RATE_LIMIT_SECURITY_REPORT.md`
- `render.yaml`
- `POSP_COMPLETION_AUDIT.md`
- `POSP_FINAL_COMPLETION_REPORT.md`

## Deployment and remaining work

- CI's Redis cross-worker test is pending.
- The changes have not yet been pushed/merged or deployed.
- After successful CI and deployment, verify the Render service commit, then
  check production `/health` and strict `/readiness`. Do not test quota limits
  by flooding production endpoints.
- Confirm the masked production `RATELIMIT_STORAGE_URI` hostname maps to the
  existing named Valkey resource without copying credentials into logs,
  responses, or reports.
