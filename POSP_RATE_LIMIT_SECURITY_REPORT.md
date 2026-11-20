# POSP Distributed Rate-Limiting Security Report

## Status

Implementation, local and CI verification, merge, and deployment are complete.
The production service is live at merge commit `c730b8c`; post-deployment
`/health` and strict `/readiness` checks passed. Production quota thresholds
were not probed with repeated requests, to avoid locking out legitimate users.

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
- After this remediation was deployed, production `/health` and strict
  `/readiness` both returned HTTP 200. Readiness reported all ten checks true,
  including `shared_rate_limit_connectivity=true` and
  `shared_rate_limit_storage=true`. This endpoint PINGs the configured
  `RATELIMIT_STORAGE_URI`; it does not reveal the URI.
- The exact secret URL was not copied into this report. An exact hostname
  comparison between the service's masked environment variable and the
  dashboard resource is not independently recorded.
- CI run #1017 provisions Redis 7 and passed the test that independent limiter
  instances (simulating workers) share counters and use separate
  remote-address keys.
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
| Redis cross-worker integration | **Passed in CI #1017** against Redis 7; skipped locally because no Redis server is installed |
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

- PR #260 was merged into `main`; merge commit
  `c730b8c4058adc0b8843cb4dab78641ca919caba`.
- Render confirms commit `c730b8c` deployed successfully and is live.
- Post-deployment checks at 11:08 IST on 2026-11-15 returned HTTP 200 from
  `/health` and strict `/readiness`; all ten readiness checks passed, including
  the shared limiter storage and connectivity checks.
- Confirm the masked production `RATELIMIT_STORAGE_URI` hostname maps to the
  existing named Valkey resource without copying credentials into logs,
  responses, or reports. The current report confirms a successful PING to the
  configured URI but does not independently record an exact hostname match.
- Production quota thresholds were not probed by repeated requests; limits
  were measured locally and shared-counter behavior was verified in CI.


## 2026-11-19 verification boundary (append-only)

- No rate-limit implementation change was made in this run. The pinned Flask-Limiter version remains 2.9.0; the constructor registers the intended 500/hour and 2,000/day defaults; explicit login/registration/password-reset limits remain; the backend reads `RATELIMIT_STORAGE_URI`; and the documented bounded outage policy remains five minutes of per-process fallback for ordinary limited routes with immediate fail-closed authentication and fail-closed behavior for other limited routes after the window.
- The last full live strict-readiness/shared-Valkey PING evidence remains 2026-11-15 (10/10 checks). No fresh production connectivity probe or quota stress test was run. Main `/readiness` performs a database check; main `/api/jobs` is DB-backed and may trigger background sync. Do not call either endpoint or manually run the current `production-smoke.yml` under the absolute production-database no-touch rule.
- The latest main production scholarship smoke run `44295458327` failed on 2026-11-18 because `/api/scholarships/` did not return valid JSON within 24 attempts; the first request timed out after 30 seconds. This is a production API availability/response failure, not evidence of a rate-limit quota failure.
- PR #268 adds DB-free `/health/rate-limit` and `/health/dependencies` probes and changes the public jobs API to a read-only verified snapshot. Exact-head CI `43952859017` and E2E `43952858934` passed on head `fb1b1ed5a0e4f1021c1044c141fb5152d81a4e64`, but the branch is 41 ahead / 6 behind current main and non-mergeable. Its SBI URL change to `/current-openings1` still requires live official-source proof before merge. These probes are not deployed; do not report fresh shared-store connectivity until they are deployed and checked.
- No production rate-limit flooding, database access, Key Value creation/deletion/reconfiguration, secret change, merge, or deployment occurred.


## 2026-11-21 rate-limit revalidation

Run timestamp: 2026-11-21 01:18 IST. This section records a read-only revalidation; no rate-limit configuration or secret was changed.

### Current implementation on main

- Latest inspected main is `8d92d831151350195bfeb0c4d72b1e831d1720d6`. The current backend requirements pin `Flask-Limiter==2.9.0`.
- `backend/app/utils/limiter.py` reads `RATELIMIT_STORAGE_URI` (not `REDIS_URL`) and constructs the shared limiter with global defaults `2000 per day` and `500 per hour`. `/health` and `/readiness` are explicitly exempt. The explicit route-specific login, registration, and password-reset limits remain in place.
- The documented outage policy uses Flask-Limiter's bounded in-memory fallback for at most 300 seconds. Authentication routes fail closed immediately when shared storage is missing or degraded; other non-operational routes retain local rate limiting only during that bounded window and then return 503. Health/readiness probes remain available so operators can detect the failure.
- Strict readiness evaluates dependency checks and returns a non-ready status when any required dependency is unavailable. The implementation uses the pinned Flask-Limiter 2.9.0 storage-degraded state and is covered by focused tests.

### Verification evidence and remaining gaps

- PR #260 merged as `c730b8c4058adc0b8843cb4dab78641ca919caba`; exact-head CI 43706405080 and authenticated E2E 43706405135 both passed. The rate-limit unit and Redis integration tests are present on main. This run did not rerun tests or trigger a new CI workflow.
- The current unit suite covers the app's hourly default, explicit authentication limits, fallback behavior, immediate authentication fail-closed behavior, the 300-second cutoff, and recovery. The daily 2,000-request assertion currently uses a separate test Limiter instance rather than exercising the full application limiter with both defaults together; add an application-level daily-default regression test before treating the combined global quota as fully proven.
- Render Key Value `public-online-service-provider-rate-limit` is present and reports status `available`. The current service environment is not exposing secret values, and no secret was read or changed.
- The latest backend deployment is `dep-dc01upsipgvc738sa5g0` from main `8d92d831151350195bfeb0c4d72b1e831d1720d6`. Render logs show production pre-migration, Alembic migration, seed, and snapshot import tasks skipped because `SKIP_DATABASE_BOOTSTRAP=1`. Liveness `/health` returned 200 in Render logs.
- `/readiness` was deliberately not called in this run because its production check includes the application database and the owner has prohibited production database connections. The Key Value instance's `available` state is not a Redis PING. Therefore current shared Redis connectivity is **not reverified** in this run; the earlier successful readiness result remains historical evidence only.
- PR #268 adds database-free `/health/rate-limit` and `/health/dependencies` probes with tests that assert no database connection. Its exact-head CI 43952859017 and E2E 43952858934 passed, but its head is 41 commits ahead / 10 behind current main and the PR is not mergeable. Rebase and revalidate it before using these probes in production.

### Status

No production database connection, migration, write, rate-limit secret change, Key Value creation/deletion, merge, or deployment was performed by this rate-limit audit. Current Redis connectivity remains unverified until a database-free rate-limit health probe is merged and deployed.
