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


## Follow-up verification — 2026-11-16
- No rate-limiter code change was introduced by PR #261 or the job snapshot commit `e6859cd66bfdac646f58a7ffcbfac9b52dab09b1`; the PR #260 implementation remains the current code path. The latest backend deployment is live on that snapshot commit and Render health returned HTTP 200; the job workflow's live API probe passed.
- Readiness and shared Redis/Valkey connectivity were not re-probed after the latest deployment. Retain the prior 2026-11-15 10/10 readiness evidence as the last confirmed result; do not describe it as a fresh 2026-11-16 readiness check.
- Deployment-safety note: the backend auto-deploy start command executed `pre_migrate.py`, `flask db upgrade` and `python seed.py`; logs showed database revision `20261114_26` and the 136-service catalog-ready message. No database contents were queried in this audit, and any seed/migration data effect is unverified. Under the production no-database-touch rule, block further backend deployments until an owner-authorized DB-free start/deploy path is available.

## 2026-11-17 continuation — current deployment and safe verification boundary

- Current main 3dd43c6d66e092f1ee95e2c8a5136c864e5b3f27 is live on Render backend deploy dep-dbtllujncjis73dop00g. The deployed start command sets SKIP_DATABASE_BOOTSTRAP=1; logs explicitly skipped pre-migration, Alembic upgrade, seed and snapshot import at 2026-11-16 19:36:38Z–19:36:56Z. This run made no production database connection or query.
- The existing Key Value resource public-online-service-provider-rate-limit is available (Valkey 8.1.4); no resource was created, deleted or reconfigured.
- Current code still constructs Flask-Limiter 2.9.0 with default_limits=('2000 per day','500 per hour'), uses RATELIMIT_STORAGE_URI (not REDIS_URL), preserves explicit authentication limits, and bounds process-local fallback to five minutes. Authentication fails closed immediately on shared-store outage; other rate-limited routes fail closed after the fallback window. No production quota flood test was run.
- Live /health returned HTTP 200 / {"status":"ok"}. The prior 2026-11-15 strict readiness result (10/10 checks, shared storage and connectivity true) remains the last confirmed shared Valkey PING. Do not re-run /readiness under the current no-production-database-touch rule because it performs a database SELECT.
- Open PR #268 at head 70342642bc7c8f7a3ef9e66ff38a5fa46688a2ac adds DB-free /health/rate-limit and /health/dependencies endpoints and updates production smoke to verify shared storage and external dependencies without database access. Exact-head CI run 43952044459 and authenticated E2E 43952044707 were in progress at the checkpoint. Do not report production shared-store connectivity as freshly verified until those endpoints are deployed and return healthy.
- Previous PR #268 head 0309594bd4daaa2fbe011b4f02e9688860e51689 failed its lint step before pip-audit ran. Follow-up commit 70342642... fixes the unused-import/path errors and scopes Ruff away from the repository's legacy E701/E702 one-line style; the new exact-head run must complete the dependency audit before merge.
