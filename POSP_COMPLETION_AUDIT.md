# POSP Completion Audit

**Audit date:** 2026-11-15  
**Repository:** `marthanithinkumar-web/public-online-service-provider`  
**Starting branch:** `main` at `023a581ed5a88180d263cdf83ad10fd9b025b556`

This audit distinguishes code/test evidence from production behavior and from
external integrations that could not be verified without account credentials.
It is a point-in-time assessment; the final completion report records changes
made after this audit.

## Post-audit integration update

Exact-head-green PR #259 (`dccdfe4fae4037db685c55a4e50bdd072d8537ca`) and the
follow-up snapshot-integrity changes are in `main`; the resulting commits were
pushed. The daily refresh workflows committed scholarship and jobs data
(`f141af9`, `8c6e6e8`). This pass added `a818b93` and `00ccde8`; job refresh
run #126 published snapshot `a1b9716`. Commit `3ef5504` adds filesystem-safe
aliases for long job slugs. Job refresh #127 passed and pushed snapshot
`8cef1ae`, which was fast-forwarded into local `main`; the production API
matched the new snapshot digest. Scheduled refresh #128 also passed and
pushed snapshot `c5669c0`; production reports it ready with the exact digest
`f6b83268b3c650af965017f353cc28754bc9f9c283afefed3b695321fd3611fd`.
Scholarship refresh #96 also passed and committed `6964fbb`; a live API check
returned 27 scholarships, with NMMS still explicitly `deadline_today` on
2026-11-15.

Production revalidation corrected one earlier finding: the official NSP page
now explicitly lists NMMS student applications through 2026-11-15 (and
verification through 2026-11-30). On 2026-11-15 at 13:17 IST, the API marked
NMMS `deadline_today`; that is current evidence, not a verification-date
mix-up. The scholarship should leave the public feed after its student
application deadline. The live feed currently has 27 scholarships (26
verified-open and one deadline-today) and three verified-open job records.
Across the 20 job sources, six report success, eleven degraded, and three failed.
KVS and IBPS checks succeeded but yielded no published jobs; SEBI was blocked
with HTTP 530 and is degraded with four consecutive failures. The production
source registry now points DRDO-RAC to the official RAC site, but its latest
source status is failed with four consecutive failures. The parser
successfully read the official page locally and returned its expired notice,
which is not published; production source connectivity or runtime diagnostics
still require owner-authorized logs.

The frontend build now generates 173 canonical URLs, including detail pages
for all three live job records. The 237-character source slug is served through
the stable `/jobs/notice-136282380084494` route; production sitemap inclusion,
HTTP response, hydrated job content, and canonical URL were verified. Production
`robots.txt` allows crawlers to reach routes and all 12 configured private
routes return `noindex, nofollow, noarchive`. Production smoke #117 passed.
Browser E2E #470 exposed an obsolete sitemap-size threshold; the catalog-based
correction was committed in `00ccde8` and E2E #471 passed. E2E #473 and CI
#1012 passed after adding and exercising the long-slug route. A test-fixture
isolation issue found during the full-suite rerun was also corrected.

Commit `0de334e` selected the verified Gemini model, and `6de1846` recorded
subsequent production verification. Authenticated production-account checks on
2026-11-15 confirmed CI #1014 passed all three jobs and the Render API service
is live at commit `6de1846`. Render
also reports that the free instance may spin down and add 50 seconds or more to
requests. Search Console shows the sitemap submission is successful and was
last read on 2026-11-15 with 170 discovered pages; its indexing overview shows
11 indexed and 166 not indexed. The indexing report's last update (2026-11-09)
lists 164 discovered-but-not-indexed URLs and two alternate-canonical URLs.
The Meta app remains in Development mode and is unpublished; its WhatsApp use
case is configured only as an unpublished setup:
the webhook callback and verify-token fields are empty, verification is
disabled, and Meta states unpublished apps receive test webhooks only. No
production message was sent.

## Executive summary

The repository is a mature React/TypeScript + Flask/SQLAlchemy service, not an
MVP. It contains authentication and role checks, service/application flows,
fees and payments, uploads and object storage, admin/client dashboards,
notifications, official-opportunity feeds, SEO generation, backup tooling, CI,
and browser tests. Local backend tests, frontend typecheck/build, and the live
API readiness probe pass.

The largest verified gaps are external activation and incomplete source health:

- Of 20 production job sources, six report success, eleven degraded, and three
  failed. KVS and IBPS reported successful checks with zero published notices;
  SEBI remains blocked with HTTP 530 (degraded, four consecutive failures)
  and DRDO-RAC remains failed with four consecutive failures. The live job
  feed and sitemap were revalidated after refresh #128.
- NMMS is currently deadline-today per the official NSP student-application
  row, not expired as the earlier snapshot indicated. The feed must remove it
  after 2026-11-15 and continue excluding expired listings.
- `render.yaml` now selects the requested `gemini-3.5-flash-lite` model. Google's
  official catalog marks it stable, and the existing `v1beta` `generateContent`
  endpoint matches the documented API. Client AI remains disabled until a
  production credential and successful live call are verified.
- The production WhatsApp configuration endpoint reports Cloud API disabled
  and status notifications unavailable. This is not a successful production
  messaging integration.
- Search Console access confirms the sitemap is submitted, but indexing is
  incomplete: 166 URLs are not indexed (164 discovered but not indexed and two
  alternate canonicals in the latest detailed report). Meta's app remains
  unpublished with no webhook configured, and no production message was sent.
  AI provider calls still require a production credential and successful live
  request. No live payment/refund was initiated.
  The encrypted backup restore drill and Razorpay read-only production
  confirmation have passed, but these do not verify a user transaction.

## Requirements assessment

The prompt has **12 top-level requirement areas**. Their verified status is:

| Area | Status | Evidence / remaining work |
|---|---|---|
| 1. Repository audit | Partial | Inspected repository structure, current history, 288 local/remote branch refs, 10 open PRs, core docs/configuration, tests, and live endpoints. Not every historical branch diff or commit was individually reviewed. |
| 2. Preserve previous requirements | Partial | Worktree was clean at start; the current main feature set and tests were retained. No stale branch was blindly merged. |
| 3. Platform features | Partial | Existing auth, client/admin workflows, orders, fees, uploads, receipts, notifications, and management functions have implementation and backend coverage. External live user journeys and all roles were not independently exercised in production. |
| 4. Jobs and scholarships | Partial | Scheduled refresh is configured for 07:45 IST; 20 sources are configured; backend/frontend filters, snapshot integrity, deadline, and freshness rules have regression coverage. Run #128 started at 14:47 IST, over seven hours after its scheduled time. Current production status is 6 successful, 11 degraded, 3 failed. KVS/IBPS succeeded with no published jobs; SEBI remains blocked with HTTP 530 and four consecutive failures; the production DRDO-RAC registry points to the official RAC URL but reports failed with four consecutive failures. The parser reads the official RAC page locally and rejects its expired notice. Job refresh #128 passed and production matched snapshot `c5669c0` and its exact digest. Scholarship refresh #96 passed and committed `6964fbb`; the live API currently returns 27 records and NMMS remains deadline-today. Source health and schedule reliability remain unresolved. |
| 5. POSP AI | Incomplete | Existing in-client support chat and admin operations AI are present with grounded context and safe error handling. `render.yaml` now selects the requested stable `gemini-3.5-flash-lite` model, and the existing `v1beta` `generateContent` request method matches Google's API documentation. `POSP_CLIENT_AI_ENABLED` remains false because no production key or successful live call has been verified. |
| 6. WhatsApp Cloud API | Incomplete | Webhook verification/signature handling, inbound/outbound services, status updates, templates, consent, and admin monitoring are implemented and tested. Production `/api/whatsapp/config` reports disabled and notifications unavailable. The Meta app is unpublished; callback and verify-token fields are empty and webhook verification is disabled. |
| 7. SEO/indexing | Partial | Public metadata/canonicals/structured data, sitemap and robots generation, prerendering, and private-route `X-Robots-Tag` behavior are implemented. Production sitemap contains 173 URLs; all three live job detail routes, including the long-slug alias, were verified. All 12 private routes return HTTP 200 with a noindex header. Search Console confirms the sitemap is successfully submitted (170 discovered pages); its overview shows 11 indexed and 166 not indexed. The latest detailed report lists 164 discovered-not-indexed and two alternate-canonical URLs; inspect representative pages and resolve indexing causes. |
| 8. Security/reliability | Partial | Production startup rejects a missing/weak `SECRET_KEY`; auth/admin tests, input validation, upload limits, private storage, payment verification, backups, and readiness checks exist. The Flask-Limiter 2.9.0 global-default bug is fixed with constructor defaults (500/hour and 2,000/day). Redis outage fallback is process-local, preserves limits, fails auth closed, and fails other rate-limited routes closed after five minutes. The remediation is deployed at Render commit `c730b8c`; production `/health` and strict `/readiness` returned HTTP 200, with all ten readiness checks true. Restore drill #12 and Razorpay confirmation #21 passed; no penetration test or live payment/refund was performed. |
| 9. Testing/integration | Partial | Latest full local backend suite: 334 passed, one Redis integration test skipped because no local Redis server is installed, and 129 warnings. CI #1017 passed the Redis 7 shared-counter integration step and all CI jobs. Frontend typecheck/build, production smoke #120, scholarship smoke #95, CI #1012/#1014, authenticated browser E2E #478, restore drill #12, Razorpay confirmation #21, and job refresh #128 passed. External AI, WhatsApp, and live transaction/refund tests remain outstanding. |
| 10. Git/merging | Partial | 288 branches and 10 open PRs were found. Commits `a818b93`, `00ccde8`, `3ef5504`, `0de334e`, and `6de1846` were pushed; automated snapshot refreshes `a1b9716`, `8cef1ae`, and `c5669c0` were fast-forwarded locally. Historical branch contents were not all reviewed; stale PRs were not merged. |
| 11. Deployment | Partial | PR #260 was merged to `main` as `c730b8c` and deployed to the existing Render API service. At 11:08 IST on 2026-11-15, `/health` returned HTTP 200 (`{"status":"ok"}`) and strict `/readiness` returned HTTP 200 with all ten checks true, including shared rate-limit storage/connectivity. The existing Valkey 8 service remains `public-online-service-provider-rate-limit`; readiness PINGs the configured shared store. The exact secret URL was not copied or exposed, and an exact hostname comparison was not independently recorded. The API's free instance may sleep. AI and WhatsApp remain disabled. |
| 12. Final destination | Incomplete | Work is not production-complete until the external AI/WhatsApp configuration and the remaining feed/source/deployment checks are verified. |

## Verified completed behavior

- Flask authentication, client/admin authorization, order/payment handling,
  configurable fee rules, support messages, refunds, and WhatsApp workflows
  have focused backend tests.
- Official-source job/scholarship validation, deadlines, filters, snapshots,
  and scheduled refresh are implemented with regression tests.
- The merged opportunity rules use declared timezone/cutoff fields and source
  freshness, keep invalid/expired items out of public feeds, and retain audit
  records. The live job API returned three fresh SBI notices. The live
  scholarship API returned 27 records (26 verified-open, one deadline-today);
  the official NSP page confirms the NMMS student-application deadline is
  2026-11-15, while its verification deadline is 2026-11-30.
- The merged job JSON and backend SHA-256 deployment marker now match; the
  added regression test normalizes Windows line endings before comparing the
  committed snapshot digest.
- Frontend has dedicated service, jobs, scholarships, account, application,
  order, admin, and support views. Browser E2E coverage exists in CI.
- Production `/readiness` returned HTTP 200 with all ten reported checks true:
  database, persistent document storage and connectivity, shared rate-limit
  storage and connectivity, SMTP delivery/connectivity, Razorpay live
  credentials, webhook configuration, and Razorpay connectivity.
- Razorpay production confirmation #21 passed: the deployed live credentials,
  webhook, read-only API authentication, and safe public checkout response
  were verified. No payment or refund was created.
- Full encrypted database restore drill #12 passed on 2026-11-09. It restored
  and validated the latest backup in a disposable PostgreSQL instance and
  removed the disposable target and plaintext dump.
- Production frontend, API health, robots, sitemap, and private-route noindex
  header returned HTTP 200 during this audit.
- The current SEO build generated 173 canonical public URLs. Private pages are intentionally
  not blocked in `robots.txt`: crawlers must be able to read their `noindex`
  response headers. The production `/my-orders` response includes
  `X-Robots-Tag: noindex, nofollow, noarchive`.
- All three current SBI job records have prerendered detail pages. The
  237-character source slug uses the short stable route
  `/jobs/notice-136282380084494`; its production page content and canonical
  URL were verified after deployment.
- `Employment News All Jobs` is absent from the source search and the build
  includes a regression check to prevent its reintroduction.

## Broken or incomplete behavior observed

- **Priority-source health:** the latest production source endpoint reports
  six successes, eleven degraded, and three failures across 20 sources. KVS and
  IBPS checks succeeded (six and 12 fetched, respectively) with no published
  jobs.
  SEBI is blocked with HTTP 530 and is degraded with four consecutive
  failures. The `drdo_rac` registry now uses
  `https://rac.gov.in/index.php?lang=en&id=0`, but its latest production status
  is failed with four consecutive failures. The parser successfully fetches
  and parses the official page in this environment, extracting the explicit
  extended application deadline and not the later page-update date; that
  notice is expired and not published. The production cause cannot be diagnosed
  from the public endpoint, which deliberately omits failure details; use
  owner-authorized operational logs. SBI succeeded with 49 fetched and three
  published records. Failures are fail-closed, but source availability remains
  incomplete.
- **NMMS deadline point-in-time correction:** the earlier audit treated the
  NMMS record as expired based on the then-current 2026-08-31 snapshot. A
  direct fetch of the official NSP listing at 2026-11-15 13:17 IST shows
  `Student Application Open till : 15-11-2026` and verification through
  `30-11-2026`. The live deadline-today record is supported by that official
  student-application evidence. The expected expiry after 15 November remains
  covered by the offline date-expiry regression, but the next scheduled
  refresh should be checked after the deadline.
- **Production smoke:** run #115 failed only at the obsolete assertion that
  robots.txt must `Disallow` private routes. The production robots file
  correctly allows crawling so crawlers can see `X-Robots-Tag`; all 12
  private routes returned HTTP 200 with `noindex, nofollow, noarchive`. The
  workflow correction removes the contradictory assertions and retains the
  explicit private-route header checks. It is pushed in `a818b93`; smoke run
  #116 passed.
- **Browser E2E:** run #470 failed because its sitemap test expected more than
  2,000 URLs while the verified production sitemap contains 172. The test
  assertion is stale; it now checks a catalog-derived minimum and every
  catalog service URL. The fix is committed in `00ccde8`; E2E #471 passed.
- **AI activation/configuration:** `render.yaml` now selects the requested
  stable `gemini-3.5-flash-lite` model. Google's official catalog and API docs
  confirm the model and the existing `v1beta` `generateContent` endpoint.
  Client AI remains disabled because there is no verified production key or
  successful live model call. Do not describe it as operational.
- **WhatsApp activation:** production config says Cloud API is disabled. The
  authenticated Meta app dashboard shows the app is unpublished; its webhook
  callback and verify-token fields are empty and verification is disabled.
  Meta states production webhooks are unavailable until publication. Source
  implementation and webhook tests do not establish Meta activation, approved
  templates, or message delivery.
- **SEO validation:** the local build and production sitemap each report 173
  URLs, with all three current job details included. The 237-character source
  slug uses a short stable ID-based route, and the production page hydrates with
  the expected title and canonical. Search Console confirms the sitemap is
  successfully submitted with 170 discovered pages. Its overview reports 11
  indexed and 166 not indexed; the latest detailed report lists 164
  discovered-not-indexed and two alternate-canonical URLs. The data does not
  establish that those URLs are errors; inspect representative URLs and improve
  crawl discovery/content where appropriate.
- **History/branch review:** 288 branches exist, mostly historical feature/fix
  branches. The 10 open PRs were enumerated; only the latest source-freshness
  PR (#259) was selected for detailed integration because its changes directly
  address the verified live listing defect and its exact-head checks pass.

## Test/build results

- `python -m pytest -q backend/tests` from the repository root with
  `PYTHONPATH=backend`: **334 passed, 1 skipped**, 129 warnings, 135.88s.
  The one skip is the Redis cross-worker integration test; no local Redis
  server was available. CI now provisions Redis 7 and runs that test explicitly.
  Warnings include the deliberately short test JWT key and a deprecated
  `datetime.utcnow()` use in an existing test.
- `npm ci`: **100 packages installed; 0 vulnerabilities** reported by npm.
- `npm run typecheck`: **passed**.
- `npm run build`: **passed**; active-listing, job-filter, prerender, SEO,
  sitemap, canonical, and refresh-shell validations completed. IndexNow was
  skipped because opt-in was not set.
- Post-merge targeted backend regression tests for jobs, source resilience,
  scholarships, snapshots, filters, AI, and the snapshot deployment marker:
  **75 passed**.
- An initial rerun exposed three path-dependent tests when pytest was launched
  from `backend/` and three scholarship eligibility tests that reused a stale
  local SQLite schema. The eligibility tests now use the repository's isolated
  temporary-database fixture; the full root-level suite then passed.
- PR #259 exact head `dccdfe4fae4037db685c55a4e50bdd072d8537ca`: GitHub CI's
  operational safety, backend tests, frontend typecheck/build, and authenticated
  Chromium E2E checks all reported success.
- Commit `a818b93`: CI #1009 and production smoke #116 passed.
- Commit `00ccde8`: authenticated browser E2E #471 passed after correcting the
  stale sitemap-size assertion found by E2E #470.
- Commit `3ef5504`: CI #1012, production smoke #117, scholarship smoke #95,
  and authenticated browser E2E #473 passed. Production sitemap and the
  long-slug route were verified after deployment.
- CI #1014 passed all three jobs (operational script safety, backend tests,
  frontend typecheck/build) at commit `6de1846`.
- Job refresh #126 passed and published snapshot `a1b9716`.
- Job refresh #127 passed, published snapshot `8cef1ae`, and verified that
  the production API matched the exact 3-job/20-source snapshot and SHA
  `2b2ea51f95071814d3b91523772e06444b74b746abb02e211fe941085ed4ad38`.
- Job refresh #128 passed, published snapshot `c5669c0`, and production
  reports the exact 3-job/20-source snapshot ready with SHA
  `f6b83268b3c650af965017f353cc28754bc9f9c283afefed3b695321fd3611fd`.
- Scholarship refresh #96 passed and published commit `6964fbb`; production
  still reports 27 scholarships, with NMMS at its student-application
  deadline-today status for 2026-11-15.
- Restore drill #12 passed with a disposable PostgreSQL restore and validation.
- Razorpay confirmation #21 passed for live configuration, webhook, read-only
  authentication, and public checkout secret-safety checks.
- Initial frontend validation attempts before `npm ci` failed because the
  checkout had no installed frontend dependencies; the subsequent locked
  install and reruns succeeded.

## Security and external integration limits

- No credentials were copied into the report or queried from private
  configuration.
- Production readiness checks show the deployed DB, SMTP, storage, limiter, and
  Razorpay configuration are reachable. Razorpay read-only confirmation and
  the isolated restore drill passed. No live payment/refund was created.
- AI remains disabled without a production key or successful live call. The
  Meta app is unpublished and webhook setup is incomplete; no Meta message was
  sent. Render currently uses a free API instance that may sleep; changing the
  plan would require owner approval for the associated cost.
- `robots.txt` is not an access-control mechanism; private APIs remain protected
  by authentication/authorization. The frontend noindex header only controls
  indexing behavior.

## Deployment and next work

1. Investigate DRDO-RAC's four consecutive production source failures using
   owner-authorized Render logs; the production endpoint confirms the corrected
   official RAC URL but hides the error cause. Do not bypass source controls.
2. Resolve the SEBI HTTP 530 block (four consecutive degraded checks) through
   an approved official source or owner-authorized network access; verify KVS
   and IBPS parsing and keep all unavailable sources fail-closed.
3. Check that the scholarship refresh removes NMMS after its 2026-11-15
   student-application deadline and that the production API and sitemap
   converge on the following refresh.
4. Configure and verify the requested Gemini model/API with an authorized key,
   or retain the disabled flag and disclose AI is unavailable.
5. Configure Meta WABA credentials, callback verification, phone/template
   settings, and consent; perform owner-authorized inbound/outbound delivery
   tests before enabling production messaging.
6. Inspect GSC coverage, validate canonical/noindex behavior for all private
   routes and pagination, and resolve any reported indexing issues for the new
   long-slug canonical route.
7. Perform owner-authorized end-to-end payment/refund and representative
   client/admin production journeys. The isolated encrypted backup restore
   drill has passed.

The job refresh workflow is configured for 02:15 UTC (07:45 IST), but
scheduled run #128 started at 09:17 UTC (14:47 IST) on 2026-11-15, over seven
hours late. The feed was successfully refreshed, but GitHub Actions did not
meet the requested 07:45 IST timing. A more reliable scheduler requires
owner-authorized deployment configuration.

## Distributed rate-limiting remediation

- **Root cause:** the application assigned `limiter._default_limits` after
  constructing Flask-Limiter 2.9.0. That private assignment did not register
  default limit groups, so ordinary unannotated routes had no global limits.
- **Fix:** register `2000 per day` and `500 per hour` in the supported
  `Limiter(default_limits=...)` constructor, retaining route-specific limits
  and the existing `RATELIMIT_STORAGE_URI` / `get_remote_address` behavior.
- **Outage policy:** Flask-Limiter uses its logged per-process memory fallback
  for ordinary endpoints for at most five minutes. Sensitive auth-blueprint
  routes fail closed with HTTP 503 in production as soon as the shared store
  is unavailable or unconfigured. Other rate-limited routes fail closed after
  the fallback window. Readiness reports the Redis PING result and production
  strict mode returns HTTP 503 on any required dependency failure. The fallback
  is not distributed.
- **Operational routes:** `/health` is a liveness-only response and
  `/readiness` checks the database and configured dependencies; both bypass
  rate-limit quotas. Neither exposes connection details.
- **Local verification:** Flask-Limiter 2.9.0 was confirmed from the pinned
  requirement. Tests exercised the actual 500/hour and 2,000/day behavior on
  unannotated routes, login/registration/password-reset caps, health/readiness
  exemptions, storage failure, fallback, fail-closed auth, bounded fallback,
  recovery, and readiness PING failure. The full local backend suite passed
  334 tests with one environment-dependent Redis integration skip. CI #1017
  passed the Redis 7 integration step that verifies shared counters across
  independent limiter instances.
- **Merge and deployment:** PR #260 was merged to `main` as `c730b8c`
  (`c730b8c4058adc0b8843cb4dab78641ca919caba`). Render reports the deployment
  succeeded and is live on that commit. Production `/health` and strict
  `/readiness` returned HTTP 200 at 11:08 IST; readiness reported all ten
  checks true, including shared rate-limit storage/connectivity. No production
  quota flooding was performed.


## Continuity checkpoint — 2026-11-16

### POSP.zip intake and review
- The exact uploaded `POSP.zip` was accessible from the Library; no replacement archive was used. Archive size: 60,638,629 bytes. SHA-256: `306a55c63fbe23155929d6c07c915bca0e9a4a5550a7a860c74009f3477b3d0f`.
- The archive contains two independent repository roots. The outer `POSP/` root is on `codex/posp-production-reliability-fixes` at `303a61b30ea8a835705ccc1dec67141927ef2962`; GitHub compare against current main showed 142 commits ahead / 1 behind, 76 tree paths modified, and 12 current-main-only paths. No PR is associated with this branch. It lacks current WhatsApp files, verified-deadline migration 26, rate-limit tests and current audit reports. Do not merge this branch wholesale.
- The nested `POSP/public-online-service-provider/` root is on `fix/sebi-official-vacancies-source` at `982419b069b48df030cfd2462c46e1497ae204a6`. Its `priority_sources.py`, `sources.py` and `test_priority_job_sources.py` changes match PR #261 and are already integrated by merge commit `d9386e448524d31b57c608bcb9dd02e5f4e30f43`; do not duplicate them. Its other two content changes are a generated backend static index and an unrequested logo asset.
- After normalizing Windows CRLF line endings, the outer root has 16 content-modified tracked files and 11 new source/doc/test files; 342 other tracked files are line-ending-only changes. The new files are the `backend/app/ai/**` provider package, its test, `docs/AI_PROVIDER_ARCHITECTURE.md`, and a responsive jobs E2E test. The nested root has five content changes (three already merged above; two static assets) and 364 line-ending-only changes.
- The candidate AI changes are not safe to merge as supplied: the outer `render.yaml` enables `POSP_CLIENT_AI_ENABLED=true`, changes the model to `gemini-2.5-flash`, and the mocked OpenAI test hard-codes an unverified model identifier. Current main deliberately keeps client AI disabled and uses the configured Gemini 3.5 Flash Lite model. The new AI files overlap the open AI PRs #216 and #235.
- The outer `backend/app/routes/jobs.py` and `frontend/src/services/jobs.ts` versions do not preserve current official-source verification/freshness checks and would regress the current feed protections. The outer `render.yaml` is a production configuration change and is not authorized. The lockfile-only change, generated static index, sitemap, logo and old branch robots file were not integrated.
- The archive includes nested `.git` data, node_modules/build outputs, local/test database files (including `backend/instance/psp.db`) and caches. These are excluded. No high-confidence credential pattern was found in the scanned text; no database file was opened or copied.
- No archive changes were committed or merged. No archive tests were run because no unique safe code patch was identified. ZIP integration remains open; the next safe step is to reconcile the AI proposal against PRs #216/#235 while keeping client AI disabled, and port only individually verified changes onto current main.

### GitHub, CI and production deployments
- PR #261 merged at exact head `9598074c9a0a3f16f870fb90ae4ac86d9d313fde` into `d9386e448524d31b57c608bcb9dd02e5f4e30f43`. Exact-head CI run `43726642174` (#1019) and browser E2E run `43726642122` (#480) passed.
- Job snapshot workflow run `43751989944` (#130) passed and published snapshot commit `e6859cd66bfdac646f58a7ffcbfac9b52dab09b1`. Its production job-feed verification step passed.
- Current Render frontend deploy `dep-dbt0fj49v7es73cem64g` and backend deploy `dep-dbt0fj49v7es73cem570` are live on `e6859cd66bfdac646f58a7ffcbfac9b52dab09b1`. Render health check returned HTTP 200; the job workflow's live API feed probe passed. Readiness and shared Redis connectivity were not re-probed after this latest deploy; the latest recorded 10/10 readiness/shared-storage verification remains the 2026-11-15 report.
- **Production database safety blocker:** the existing backend Render start command ran `pre_migrate.py`, `flask db upgrade` and `python seed.py` during the automatic deploy. Logs reported database revision `20261114_26`, an Alembic PostgreSQL context, and `Public service catalog ready: 136 active services`. This audit did not query the production database; whether the seed command changed rows is unverified. No further backend merge/deploy should be initiated under the no-database-touch rule until an owner-authorized DB-free deployment path is in place. The job and scholarship snapshot workflows also publish to main and can trigger the same auto-deploy path.

### Expiry and feed audit
- Scholarship snapshot `frontend/public/data/scholarships.json` is generated at `2026-11-15T09:47:43.189234Z`. It contains 27 active records, including **National Means Cum Merit Scholarship** with `status=active`, `application_status=deadline_today`, student application deadline `2026-11-15`, and source check `2026-11-15T09:47:43.189234Z`. The official NSP listing states the student application deadline was 15-11-2026; 30-11-2026 is the later institute-verification deadline, not the student application deadline. On 2026-11-16 this item is expired. It remains in the deployed raw static JSON snapshot; runtime API/frontend filters and the build-time SEO generator should exclude it, but direct HTTP verification of the scholarship API/UI was unavailable in this run. The scheduled scholarship refresh is due at 02:30 UTC / 08:00 IST and must be checked for removal from the raw feed and API.
- The other 26 active scholarship snapshot records have 2026-11-30 deadlines; no other expired or deadline-today scholarship was found in this snapshot.
- The current jobs snapshot is generated at `2026-11-15T19:21:50Z` (2026-11-16 00:51:50 IST), with three published records. **SBI Specialist Cadre Officer fixed-term employment, CRPD/SCO/2026-27/30** has an official last date of `2026-11-16`; the SBI current-openings page and application portal confirm 16-11-2026. No cutoff time is published, so show “Deadline today—check official portal”, not “verified open after cutoff”. It remains in the deployed raw jobs snapshot; the current frontend logic treats a deadline-today item as non-open for sitemap/Apply purposes when no cutoff is known.
- The other two published SBI jobs have 2026-11-23 deadlines. No verified expired job was found among the three current published job records. The official SBI page currently lists five notices; POSP contains only three, so the /28 and /29 notices (both showing 25-11-2026 on the official page) are missing from the public feed and need source-parser reconciliation.
- Job source health after run #130: 7/20 successful, 3 failed (NVS, DRDO-RAC, RRB) and 10 degraded; 6,765 records remain in review. Source failures are not evidence that an opportunity is expired or open.
- PR #253 is **closed without merge**, not open. Its Beedi Pre-Matric closure is represented in the merged PR #259 scholarship data: Beedi Pre-Matric, Beedi Post-Matric and Pre-Matric Scholarship for Students with Disabilities are in backend `closed_items` with 2026-10-31 deadlines and are absent from the active frontend snapshot. API live verification for scholarship detail routes remains outstanding.
- The frontend build regenerates sitemap using current-date verified eligibility, so the 2026-11-16 build should omit the expired NMMS and deadline-today SBI detail URLs; the tracked source sitemap remains an older generated file. Direct live sitemap HTTP verification was unavailable.
 
### SEO and AI carry-forward
- `frontend/scripts/generate-seo.mjs` rewrites `robots.txt` to only `User-agent: * / Allow: /` plus Sitemap. Private-route exclusions therefore remain missing after every build. PR #251 changes only the generated output file and is insufficient unless the generator is fixed.
- Current main keeps `POSP_CLIENT_AI_ENABLED=false`; no live provider call was established. Do not enable client AI until provider/model validity, privacy redaction, synthetic end-to-end behavior and the owner's existing enablement gate are verified.
- Carry forward: verify the 08:00 IST scholarship refresh and NMMS removal; recheck SBI /30 after its published last date; restore the two missing official SBI notices; fix robots generation rather than only the output file; reconcile PRs #216/#235/#232/#251/#252 against current main; keep the production DB no-touch blocker open; and continue ZIP integration without replacing main or importing generated/local DB files.


### Copilot ZIP integration update — 2026-11-16 08:05 IST
- Re-materialized the exact Library archive `POSP.zip` and reverified SHA-256 `306a55c63fbe23155929d6c07c915bca0e9a4a5550a7a860c74009f3477b3d0f`, 9,453 entries / 8,312 files. The outer `POSP/` repository is based on `303a61b` and contains local working-tree changes, stale generated artifacts, local DB/cache/upload files and broad line-ending rewrites. The nested repository's SEBI changes are already covered by merged PR #261.
- Created safe integration branch `integration/posp-zip-safe-ui-privacy-20261116` from exact main `e6859cd66bfdac646f58a7ffcbfac9b52dab09b1`. Selectively integrated URL-driven job filter state, 120-character search input bound, client-ID-free AI error logging and a regression test. No local DB, generated snapshots, deployment config or AI enablement change was imported.
- Draft PR #263: https://github.com/marthanithinkumar-web/Public-Online-Service-Provider/pull/263. Head `66778915144ba901a170e4b190eeddf5c325d361`. Compare is 3 commits ahead / 0 behind; exactly three files changed.
- Exact-head CI: frontend typecheck/build **passed**; operational script safety **passed**; backend full suite and authenticated browser E2E were still running at this checkpoint. Do not call the PR green until both finish successfully.
- AI provider adapters/core refactor, privacy redaction in prompts, and AI health UI remain excluded from PR #263 because they overlap open PRs #216/#235 and need a consolidated review. Do not set client AI true or import the archive Render setting. The archive E2E jobs-filter test targets controls absent from current main and is not valid as-is. API/snapshot/job-source changes overlap PR #239 and are not transplanted.
- No merge, production deployment, Render configuration change, or production DB access/write/migration/seed was performed for PR #263. The production backend auto-start DB migration/seed path remains a hard merge/deploy blocker.

## 2026-11-17 — POSP ZIP, expiry, DB-safety and deployment continuation

**Checkpoint:** 2026-11-17 02:09 IST. This is an evidence checkpoint, not a completion claim.

### POSP.zip recursive inspection and reconciliation
- Re-materialized the exact uploaded POSP.zip. SHA-256: 306a55c63fbe23155929d6c07c915bca0e9a4a5550a7a860c74009f3477b3d0f. The archive contains 9,453 entries / 8,312 files and two independent repository roots: outer POSP/ (local branch codex/posp-production-reliability-fixes, HEAD 303a61b) and nested POSP/public-online-service-provider/ (local branch fix/sebi-official-vacancies-source, HEAD 982419b). Both include their own .git metadata. Do not treat the first folder as the sole repository root or replace current main with either tree.
- The archive also contains vendored dependencies/build output, caches, upload/test artifacts and a local SQLite database file. These were not imported or opened. A high-confidence text scan found no private-key, GitHub PAT, Google API key, AWS access key, Razorpay live-key or JWT pattern; this is not a substitute for secret scanning every binary/artifact.
- Safe, individually reviewed ZIP changes are already represented in merged PRs: #260 (distributed rate limiting, merge c730b8c4058adc0b8843cb4dab78641ca919caba), #261 (official SEBI source, merge d9386e448524d31b57c608bcb9dd02e5f4e30f43), #265 (safe ZIP/UI/privacy/fee/homepage/login subset, merge da7be9d7ffcd39073d485ba502879403491aea82), and #267 (Render production DB-startup hard guard, merge 772eaa39d62dc50c4e51e00e8e8962f962c12bfc). Scholarship expiry/status handling is in merged #255 (e014f50756ff59694a8a972ba768a8f648ba4ce4); deadline/freshness controls are in merged #259 (dccdfe4fae4037db685c55a4e50bdd072d8537ca).
- PR #263 is closed without merge; its safe UI/privacy subset was superseded by #265. PR #253 is closed without merge; Beedi closure was incorporated by #255 and is absent from the live active scholarship API. Do not reopen or merge stale branches blindly.
- The remaining ZIP AI provider/core refactor is intentionally not integrated. It overlaps open #216/#235/#226/#227 and must remain separate until provider/model access, privacy redaction, synthetic end-to-end behavior and the owner's enablement gate are verified. POSP_CLIENT_AI_ENABLED=false remains unchanged.

### Current code integration branch
- PR #268: fix/posp-readonly-job-snapshot-and-robots-20261117, base main 3dd43c6d66e092f1ee95e2c8a5136c864e5b3f27, current head 70342642bc7c8f7a3ef9e66ff38a5fa46688a2ac. It is open and unmerged.
- The PR makes the public jobs list/detail/source/snapshot-status endpoints read only from the verified static snapshot, moves AI job context to that snapshot, adds DB-free /health/rate-limit and /health/dependencies probes, switches SBI to the official current-openings1 page, and checks crawlable robots plus private-route X-Robots-Tag configuration.
- Follow-up commit 70342642bc7c8f7a3ef9e66ff38a5fa46688a2ac updates eight files: .github/workflows/ci.yml, .github/workflows/production-smoke.yml, backend/app/main.py, backend/app/routes/ai_operations.py, backend/app/jobs/priority_sources.py, backend/tests/test_job_notifications.py, backend/tests/test_sbi_current_openings_source.py, and frontend/scripts/verify-robots-rules.mjs. It fixes the previous Ruff job's nonexistent test path and unused imports, scopes Ruff away from legacy E701/E702 one-line-style noise, expands the SBI parser regression to four current open notices plus the expired /30 extension, and requires exact generated/live sitemap parity with eligible job and scholarship detail records.
- Previous exact-head CI run 43948322718 failed in the lint step (67 findings, mainly legacy E701/E702 plus unused imports and a missing path); backend tests, frontend build and operational-safety checks had passed. Authenticated E2E 43948322732 passed. The dependency audit did not run because lint failed first. New exact-head CI 43952044459 and authenticated E2E 43952044707 were in progress at this checkpoint. Do not merge until all required checks pass on the final exact head and main is revalidated.

### Production deployment and database safety
- Current main 3dd43c6d66e092f1ee95e2c8a5136c864e5b3f27 is live on both existing Render services: frontend deploy dep-dbtllujncjis73doovt0 and backend deploy dep-dbtllujncjis73dop00g. No new Render service or Key Value resource was created.
- The backend start command still lists pre-migration, Alembic, seed and snapshot-import commands, but the deployed SKIP_DATABASE_BOOTSTRAP=1 guard stopped each before database work. Render logs: pre-migration skipped at 2026-11-16T19:36:38.511338455Z; Alembic skipped at 19:36:51.622625881Z; seed skipped at 19:36:53.61762656Z; snapshot import skipped at 19:36:56.41188499Z. Gunicorn then booted and the backend became live. This run did not connect to, query, write, migrate, seed, import into or otherwise touch the production Neon database.
- The existing Render Key Value resource public-online-service-provider-rate-limit (ID red-dadckemk1f9s73cmq87g) is available, Valkey 8.1.4. No create/delete or configuration change was made.
- Live backend /health returned {"status":"ok"}. Do not call /readiness or the current main /api/jobs route: the former executes a database SELECT and the latter is still DB-backed until #268 is merged/deployed. The new DB-free probes and read-only jobs API in #268 will allow safe post-deploy verification.

### Official deadline and public-feed audit
- Current live job snapshot: generated 2026-11-16T19:30:32Z, 2 published jobs, both with 2026-11-23 deadlines; source check 2026-11-16T19:30:32Z. The 20-source registry reports 5 success, 11 degraded and 4 failed; 6,793 records remain in review. SBI fetched 49 and published 2; KVS 6/0, SEBI 4/0, IBPS 9/0, Wipro 6,744/0. Failures/degraded parses are not proof of continued openness or expiry.
- The official SBI current-openings1 page, checked 2026-11-17 about 02:09 IST, lists four open notices: AD29 Assistant Manager Engineer (Fire), deadline 2026-11-25; AD28 Manager (Security)/Deputy Manager, deadline 2026-11-25; AD26 Chief Manager/Manager Product & Research, deadline 2026-11-23; and AD27 Risk Specialist, deadline 2026-11-23. POSP currently contains only AD26 and AD27. PR #268 changes the source URL and its new deterministic parser test requires all four active notices while excluding expired AD30. Refresh and verify after merge.
- SBI AD30 fixed-term notice CRPD/SCO/2026-27/30 has an official extended last date of 2026-11-16. It is expired on 2026-11-17. It is absent from the live jobs snapshot and live sitemap; its old tracked generated sitemap source still contains the stale detail URL. The old detail URL did not return the requested job page on live fetch; an HTTP 404 was not exposed, so do not claim that exact status.
- Current live scholarship API returns 27 active official records, all with student-application deadline 2026-11-30 and source check 2026-11-16T14:14:44.354364Z. ?q=beedi returns zero; the NMMS detail API returns {"error":"Scholarship is unavailable or applications have closed."}. The official NSP page checked 2026-11-17 about 02:09 IST says NMMS student applications closed 2026-11-15; 2026-11-30 is the later institute-verification date, not the student application deadline. NMMS is absent from the live API, static snapshot and live sitemap. Beedi records and Pre-Matric Scholarship for Students with Disabilities are also excluded from the active API.
- The live sitemap build log reports 2 eligible jobs, 27 eligible scholarships, 172 canonical public URLs and 172 pre-rendered pages. A live sitemap fetch confirms 2 job detail URLs and 27 scholarship detail URLs, with no SBI /30 or NMMS detail URL. The tracked GitHub frontend/public/sitemap.xml remains stale until regenerated at build; #268 adds build-time and production smoke parity checks.
- Daily expiry result: no verified expired or deadline-today item was found in the live public active snapshots, scholarship API or live sitemap. Newly expired SBI AD30 (last date 2026-11-16) and NMMS (student application closed 2026-11-15) are confirmed removed from those live surfaces. SBI job API-level exclusion remains unverified because the current main route is DB-backed and was not called under the no-touch rule.
- Current robots.txt intentionally permits crawlers to fetch X-Robots-Tag headers; Render YAML defines 13 private-route noindex, nofollow, noarchive patterns. The live page fetch did not expose response headers, so live header verification remains pending the DB-free production smoke after #268.

### SEO, rate limiting and AI carry-forward
- POSP Search Console was not rechecked in this run. Last recorded report (2026-11-15) showed the sitemap submitted, 170 discovered pages, 11 indexed and 166 not indexed; recheck after the new 172-URL sitemap has been live long enough to be recrawled.
- The live rate-limiter code uses Flask-Limiter 2.9.0 constructor default_limits of 500/hour and 2,000/day and reads RATELIMIT_STORAGE_URI, not REDIS_URL. Login/registration/password-reset route limits remain explicit. The bounded fallback is per-process for at most five minutes; authentication fails closed immediately and other rate-limited routes fail closed after the fallback window. /health and /readiness are exempt; #268 adds DB-free rate-limit/dependency probes. The prior 2026-11-15 strict readiness/Redis PING evidence remains the last full shared-store connectivity check; do not call DB-backed /readiness for a fresh check.
- POSP client AI remains disabled; the configured Gemini 3.5 Flash Lite path has no new live provider-call evidence. Do not merge provider/model branches or enable client AI without the explicit model, privacy, synthetic end-to-end and owner gates.

### Next safe steps
1. Wait for CI 43952044459 and E2E 43952044707 on exact head 70342642...; inspect any failed job logs and rerun only after fixing the cause.
2. Revalidate current main and all open overlapping PRs immediately before merge. Do not merge #239/#232/#251/#252 or AI provider PRs as-is.
3. After #268 is exact-head green and main is still the recorded base, merge only through the approved GitHub PR workflow. Recheck Render service config and deployment state first.
4. Deploy the existing frontend and backend services only after the DB-free startup guard is confirmed; do not call /readiness, migrate, seed, import or otherwise touch Neon.
5. Run the DB-free production smoke, verify the jobs API snapshot fingerprint, job/scholarship API eligibility, sitemap parity, private-route headers and shared Valkey connectivity. Then run the official-source refresh and confirm SBI AD28/AD29 are published while AD30 stays excluded.
