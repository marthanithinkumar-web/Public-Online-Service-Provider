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

## 2026-11-16 — Copilot ZIP review, fee correctness, login UX and startup database safety

### Archive reconciliation
- Re-materialized the exact uploaded POSP.zip. SHA-256: 306a55c63fbe23155929d6c07c915bca0e9a4a5550a7a860c74009f3477b3d0f; 9,453 ZIP entries / 8,312 files. The archive contains an outer working repository based on 303a61b and a nested repository based on 982419b.
- The nested repository's only substantive code changes (SEBI source parsing and regression coverage) are already present through merged PR #261. The package-lock updates are already present on current main.
- The outer working tree includes widespread line-ending rewrites, generated sitemap/snapshot/build files, local DB/cache/upload artifacts, and an AI provider refactor. The AI refactor was not copied: it defaults to an unverified gpt-6-luna model, overlaps existing AI PRs #216/#226/#227/#235, and its Render YAML enables client AI contrary to the currently disabled production setting. It must be reconciled after the existing AI work is consolidated and validated.
- The obsolete responsive jobs E2E test was not copied unchanged because its featured/deadline controls do not exist in current main's Jobs UI. A replacement E2E test now targets the actual search/type/location/qualification/sort controls.

### Included code fixes in this branch
- Scholarship admin fee updates now update every service whose name or category identifies it as a scholarship service, not only the canonical Scholarship Application Assistance row.
- New scholarship orders now read the current scholarship_assistance_fee_inr setting server-side, so stale browser/catalog prices cannot determine the charged assistance fee. Existing submitted orders retain their original fee.
- The scholarship payment guard now covers all scholarship service/category variants, requires authentication/ownership before returning a guard result, and rejects official-fee/combined-fee payment attempts.
- The client payment breakdown identifies all scholarship service aliases as assistance-only. Public scholarship fee and homepage fee responses use Cache-Control: no-store; public service catalog refreshes the configured scholarship fee before displaying scholarship service-card prices. Admin service management reloads its catalog after a fee change.
- Homepage now fetches and displays the configured homepage assistance fee. Scholarship request pages fetch the current public fee before showing the fee summary.
- Client and admin login now await the existing Render health warm-up before sending credentials, and display a connection status while the service is waking. Allowed API CORS preflight responses are cached for 600 seconds to reduce repeated OPTIONS round-trips; the origin allowlist is unchanged.
- The live jobs API now enforces location and qualification filters as well as existing search/type/featured filters; this closes a mismatch where the frontend API fallback previously ignored two active UI filters. Job URL state and 120-character search limits are synchronized.
- AI provider error logs no longer include client database IDs.

### Production database safety
- Current Render backend service configuration (service srv-da1k2r01ne8s73ck0io0) starts with SKIP_DATABASE_BOOTSTRAP=1 and then invokes pre-migration, Alembic, seed, and snapshot-import commands before Gunicorn.
- Added explicit early exits to those four startup tasks when the existing flag is set. The Flask app factory already skips database bootstrap under the same flag. Added a subprocess regression test using a temporary SQLite path to prove these startup commands do not create/connect to that database when the flag is set.
- Alembic migration skipping is conditional on the production flag without the explicit POSP_ALLOW_DATABASE_MIGRATIONS=1 opt-in. Only the CI migration-chain job sets that opt-in while pointing at an isolated SQLite file; Render does not set it. This preserves a real CI migration-chain test while keeping production startup DB-free.
- No production database URL was read, no production DB connection was made, and no migration/seed/import/backfill or data modification was performed. No Render service configuration, environment variable, database, or Key Value setting was changed.

### Verification state
- New backend tests cover scholarship fee propagation to multiple service variants, dynamic fee capture for new orders, preservation of existing order fees, official-fee payment rejection, anonymous payment-probe rejection, public fee no-store headers, and database-free Render startup.
- New E2E tests cover homepage fee display, current scholarship service-card fee, client/admin login warm-up ordering, and the actual responsive jobs filters.
- Exact-head CI, authenticated E2E, merge, both Render deployments and post-deployment checks are pending. Do not call this branch verified until all exact-head checks finish green. Do not claim production fee behavior or login latency is fixed until live verification.
- Render remains on the existing free plan. Cold-start duration can still depend on Render's free-instance wake-up time; the change prevents login from racing the wake-up and makes the wait visible, but does not change plan/billing.
- The separate official-source expired jobs/scholarships blocker remains open. This work does not certify the live active listing set as clean.

### Verification rerun note — 2026-11-16
- First CI attempt at commit c12531c45e4cc88e540b01b6842f2fc76e0dd5d6 passed backend tests, frontend typecheck/build and operational script safety. Browser E2E failed only on ambiguous responsive form selectors (two Search services inputs and two Password labels); those test selectors were corrected to target the first visible input.
- Added further coverage for scholarship services whose service name is generic but whose category is Scholarships & Student Welfare; order metadata now records the server's scholarship classification so the payment UI and payment guard agree.
- The exact latest integration branch is fix/posp-fees-home-auth-zip-integration-verified-20261116, forked from code head 0d6f5ac61c5787560ad36cf30a002325969d739f. A fresh PR is being opened so all required workflows execute against the final head. Earlier draft PR #264 is superseded and will be closed after the replacement PR is open.
- Do not use the earlier passing CI as final verification: the latest fee/category changes and corrected E2E selectors require a fresh full CI + browser E2E run.

- Second browser run on 475ee714 had 26 passing tests and one test-only selector failure: the accessible label Search services first matched the header navigation link rather than the actual input. The test now targets #service-search input[type=search]. The login warm-up and responsive jobs tests passed in that run; the final head must rerun all checks.

## 2026-11-16 — Render startup database incident and hardening

- After PR #265 merged (commit da7be9d7ffcd39073d485ba502879403491aea82), the first rolling backend deployment dep-dbtguv15efls73fsrs2g had a legacy instance start with the previous release. Render logs show that instance ran the pre-migration/Alembic startup and the snapshot importer reported: "Verified job snapshot imported: 3 active published job(s), 20 configured source(s)." This confirms a production DB write occurred. The log also reported database revision 20261114_26 and no "Running upgrade" line was found; no schema migration is evidenced. Seed-write activity cannot be ruled out from available logs.
- The new-release instance in the same rollout logged skips for pre-migration, seed and job snapshot import. A subsequent snapshot-refresh deployment dep-dbth05k9v7es73d1u1o0 on commit cd6f0d261ce3d18da48bba1b3b1003a70a622c93 logged skips for pre-migration, Alembic migration, seed and snapshot import, with no PostgreSQL Alembic context or snapshot-import result. This demonstrates the current SKIP_DATABASE_BOOTSTRAP guard works on the current release.
- No direct database inspection, rollback, repair or additional DB access was attempted after discovering the import. Do not attempt to reverse the imported records without explicit owner authorization. The incident must be disclosed; do not claim the absolute no-production-DB-touch rule was fully maintained during the first rolling deployment.
- Added hardening branch fix/render-no-db-startup-hard-guard-20261116. A centralized startup guard now treats Render's RENDER=true or RENDER_SERVICE_ID as an unconditional production DB-startup block for app bootstrap, pre-migrate, Alembic, seed and snapshot import. CI's isolated SQLite migration check remains enabled only outside Render via its explicit POSP_ALLOW_DATABASE_MIGRATIONS=1 opt-in.
- A parameterized subprocess regression test covers SKIP_DATABASE_BOOTSTRAP, RENDER=true with migration opt-in, and RENDER_SERVICE_ID with migration opt-in, using only temporary SQLite paths. PR/CI/deploy evidence to be appended after verification.


## Continuity checkpoint — 2026-11-19 01:35 IST (append-only)

### POSP.zip intake
- The exact `POSP.zip` attachment was not accessible in this conversation: the exact-name Files search returned no attachment bytes. No Library copy, previous-run copy, or alternate archive was substituted. The previously recorded SHA-256 `306a55c63fbe23155929d6c07c915bca0e9a4a5550a7a860c74009f3477b3d0f` is historical evidence from an earlier run only; it was not re-opened or used as this run's input. Re-upload the exact `POSP.zip` before continuing archive-by-archive comparison. No ZIP changes, commits, merges, or deployments occurred in this run.

### Current repository and PR state
- Latest inspected `main`: `f7a35955d7c6b1169ac8fd6976af4636f2609013`.
- PR #268 remains open at head `fb1b1ed5a0e4f1021c1044c141fb5152d81a4e64`; compare against current main is diverged, 41 commits ahead / 6 behind, merge base `3dd43c6d66e092f1ee95e2c8a5136c864e5b3f27`, and GitHub reports it non-mergeable. Exact-head checks are green: CI run `43952859017` (backend tests, lint/dependency audit, frontend typecheck/build, operational safety) and authenticated Chromium E2E run `43952858934`. These green checks are for the old PR head, not current main-integrated code.
- PR #268 makes the public jobs endpoints and AI job context snapshot-based, adds DB-free health probes, and replaces DB-dependent production smoke checks. However, it changes the SBI source URL from `/web/careers/current-openings` to `/web/careers/current-openings1`. The official `/web/careers/current-openings` page fetched on 19 Nov lists four current notices (/29, /28, /26, /27); the PR's new test uses a synthetic fixture and does not prove the alternative URL returns the same current notices. Do not merge until the source URL is validated against live official content and the branch is safely reconciled with current main.
- PR #262 is not documentation-only despite its title: it changes 39 files, including backend/frontend code, snapshots, startup and workflow files. Its head `8b3263f91bb88837d4e0231d84021d443ece2f40` is 6 commits ahead / 6 behind current main and diverged from base `e6859cd66bfdac646f58a7ffcbfac9b52dab09b1`. Do not merge it wholesale. This checkpoint is being carried in a separate docs-only branch from current main.
- PR #253 is closed without merge. Its Beedi closure is represented in merged PR #255 (merge `e014f50756ff59694a8a972ba768a8f648ba4ce4`) and the current backend closed audit; do not reopen or merge stale PR #253.

### Current committed opportunity snapshots and official-source audit
- Jobs snapshot `frontend/public/data/jobs.json` was generated `2026-11-18T10:04:07Z`, contains 3 active records, and has source health 8 success / 9 degraded / 3 failed across 20 sources. Failed sources are NVS, DRDO-RAC and RRB; degraded sources include Sainik Schools, MHA, TGPRB, India Post GDS, India Post, ISRO, NCS, Infosys and Accenture. Failures are not evidence of continued openness or expiry.
- The three committed active jobs are SBI CRPD/SCO/2026-27/26 (23 Nov), SBI CRPD/SCO/2026-27/27 (23 Nov), and the SSC Grade C Stenographers Limited Departmental Competitive Examination, 2026 (8 Dec; departmental/eligible-staff-only). The official SBI current-openings page checked 19 Nov 2026 about 01:35 IST lists four current openings: /29 Assistant Manager Engineer (Fire) and /28 Manager (Security)/Deputy Manager (Security), both due 25 Nov; /26 and /27, both due 23 Nov. POSP's committed active snapshot is missing /28 and /29. SBI /30 (CRPD/SCO/2026-27/30) has an official extended last date of 16 Nov and is absent from the committed active snapshot. Live API/detail/sitemap exposure for /30 and inclusion of /28-/29 could not be confirmed in this run.
- Backend and frontend scholarship snapshots were generated `2026-11-18T10:33:45.771675Z`. Both expose 27 active records, all with student-application deadline 30 Nov 2026. The backend audit additionally retains 4 closed and 6 unverified records; the frontend public snapshot contains only the 27 active records.
- The official National Scholarship Portal page checked 19 Nov about 01:35 IST confirms the closed student-application dates: Beedi/Cine/IOMC/LSDM Pre-Matric (31 Oct), Beedi/Cine/IOMC/LSDM Post-Matric (31 Oct), Pre-Matric Scholarship for Students with Disabilities (31 Oct), and National Means-cum-Merit Scholarship (15 Nov). Later institute/department verification dates are not student application deadlines. These four records are in backend `closed_items`, not the committed active frontend snapshot. PM-USP CSSS is now shown by NSP as open through 30 Nov and is present in the 27-record active snapshot.
- **Expiry result:** No verified expired or deadline-today item is present in the current committed active jobs or scholarship snapshots. This is not a live-production cleanliness claim: the API and static production URLs were inaccessible to the web retrieval path, and the latest production scholarship smoke failed (details below). Continue alerting on SBI /30 (last date 16 Nov) and the four closed scholarships until public API, detail, sitemap and AI exposure are verified removed.
- Telangana ePASS Post-Matric page checked 19 Nov explicitly states “Last Date For Fresh and Renewal Registrations is 31-03-2027” and exposes separate fresh/renewal registration links. The current parser still leaves the Fresh and Renewal records unverified because it does not normalize that deadline/evidence. This is a concrete next parser/test correction; do not silently change the current snapshot without a verified code path. Other-State Post-Matric has no item-specific deadline on the page; Pre-Matric source returned 404; Ambedkar Overseas Vidya Nidhi for SC has no explicit current deadline/status. Keep those four records unverified. Closed BC/EBC/minority overseas registrations must remain excluded.
- Scholarship source health at the last committed refresh: NSP and three ePASS sources succeeded; JnanaBhumi failed with HTTPError, Social Justice with ConnectTimeout, and Tribal Affairs with SSLError.

### Production safety and deployment verification boundary
- Main's `.github/workflows/production-smoke.yml` still calls DB-dependent `/readiness` and `/api/jobs`. Do not manually dispatch or rerun that workflow under the no-production-database-touch rule. PR #268 replaces these with DB-free probes and a read-only snapshot API, but is not merged/deployed.
- Main's `Production scholarship discovery smoke` run `44295458327` failed on 18 Nov: the first `/api/scholarships/` request timed out after 30 seconds and all 24 attempts failed to obtain valid JSON; downstream checks were skipped. The earlier `Production public smoke checks` run `44283008991` passed on 18 Nov 10:11Z, but it is not fresh evidence for the later timeout. Web retrieval also could not access live `/health`, static feeds, `robots.txt` or sitemap. No current Render deployment state was rechecked and no deployment was triggered.
- No production database was connected to, queried, written, migrated, seeded, imported, or otherwise modified by this run. Do not call main's DB-dependent `/readiness` or `/api/jobs`; use the DB-free probes only after the corrected PR is merged and deployed through the approved workflow.
- The rate-limit implementation remains Flask-Limiter 2.9.0 with constructor `default_limits` (500/hour and 2,000/day), explicit auth limits, `RATELIMIT_STORAGE_URI`, explicit health/readiness exemptions, and the bounded five-minute per-process fallback; auth routes fail closed immediately and other limited routes fail closed after the fallback window. The last full live shared-Valkey readiness/PING evidence remains 15 Nov. No fresh live connectivity or quota test was performed because current readiness is DB-dependent and production quota flooding is unsafe.

### SEO, AI and other website continuity
- POSP `render.yaml` configures private-route `X-Robots-Tag: noindex, nofollow, noarchive` patterns. `robots.txt` intentionally allows crawling so crawlers can see those headers; do not add blanket Disallow rules that prevent crawlers from seeing noindex. PR #268 adds a verification script for the headers. Live response-header verification remains blocked by production endpoint access.
- MNK Technologies main repository commit `21d3355e026336c9d3db8b6301bcc512b89ceb28` has no open PRs/issues. Source metadata includes canonical, title/description, Open Graph/Twitter and Organization/WebSite structured data; robots allows crawling and sitemap contains the homepage. Render deployment was not rechecked in this run.
- FileWeave main commit `4a47a8dc7831153ed3d954b0fdba642e85541140` has a successful Vercel status. Its canonical is `https://fileweaveonline.vercel.app/`, robots allows crawling, and the sitemap has 12 URLs with 10 generated SEO pages. The hyphenated `file-weave.vercel.app` is not the canonical domain. PR #88 head `52e8e214acdb3595994242c2064ab7a7e4464f83` remains open; exact-head `verify` failed in run `44387247430` at `clearActivePipeline` timeout after preceding production acceptance tests passed. Vercel Preview Comments passed. Owner manual-acceptance issue #12 remains open (0/10); do not mark FileWeave complete or merge #88.
- POSP's configured model remains `gemini-3.5-flash-lite`, which is present in Google's current model catalog. Groq is not integrated. Groq GPT-OSS 120B advertises ~500 tokens/sec, but its documented developer limits include 30 RPM, 1,000 RPD and 8,000 TPM; speed alone is insufficient evidence for a production switch. Keep Gemini primary pending a grounded quality/latency/cost benchmark. `render.yaml` declares `POSP_CLIENT_AI_ENABLED=false`; the actual Render runtime value was not checked. Do not change provider or enablement settings in this run.

### Run outcome
- No application code, snapshots, production configuration, database, or service was changed. No merge/deployment occurred. This checkpoint records read-only evidence and unresolved blockers; all production and feed-correctness blockers remain open.


## 2026-11-21 run audit

Run timestamp: 2026-11-21 01:18 IST. This section is append-only.

### Copilot ZIP inspection and disposition

- Exact Library attachment `POSP.zip` was accessible and inspected recursively. SHA-256: `306a55c63fbe23155929d6c07c915bca0e9a4a5550a7a860c74009f3477b3d0f`. Layout contains an outer working repository at `POSP/` and a nested repository at `POSP/public-online-service-provider/`; the nested repository root was not assumed from the first folder.
- The nested repository contained 379 relevant source, test, documentation, and configuration files after excluding Git metadata, dependency trees, caches, generated builds, local databases, and archive artifacts. After normalizing Windows CRLF to LF, 342 matched current main and 37 differed. The differences were reconciled against current main and the open PR set; the nested SEBI parser change is already represented by PR #261.
- The archive contains local SQLite/test database files, uploads, caches, Git metadata, dependency trees, generated bundles and line-ending-only rewrites. These were not imported or inspected as application data. A static scan found no confirmed real credentials; the only credential-shaped match was a test-only E2E placeholder. No database contents were read.
- Safe ZIP changes already merged and deployed: PR #260 rate-limit hardening (merge `c730b8c4058adc0b8843cb4dab78641ca919caba`; CI 43706405080 and E2E 43706405135 passed); PR #261 SEBI parser (merge `d9386e448524d31b57c608bcb9dd02e5f4e30f43`; CI 43726642174 and E2E 43726642122 passed); PR #265 safe UI/filter/privacy and fee/login fixes (merge `da7be9d7ffcd39073d485ba502879403491aea82`; CI 43882543484 and E2E 43882543522 passed); PR #267 Render database-startup hard guard (merge `772eaa39d62dc50c4e51e00e8e8962f962c12bfc`; CI 43884521242 and E2E 43884521284 passed).
- The remaining unmerged Copilot provider abstraction adds `backend/app/ai/providers/*`, `backend/app/ai/text.py`, `backend/tests/test_ai_provider_architecture.py`, and `docs/AI_PROVIDER_ARCHITECTURE.md`, and changes `backend/app/ai_core.py` and `render.yaml`. Its default OpenAI model string `gpt-6-luna` is not validated; the manifest enables both `POSP_AI_ENABLED` and `POSP_CLIENT_AI_ENABLED`, while the current main configuration intentionally uses `gemini-3.5-flash-lite` and keeps client AI disabled. Do not merge or deploy this refactor until provider/model configuration, credential handling, privacy, and provider-backed tests are reviewed. It remains a specific integration blocker, not a completed feature.

### Current main and production state

- Latest inspected main: `8d92d831151350195bfeb0c4d72b1e831d1720d6` (data refresh; no code change in this commit).
- Existing Render frontend `pospindia` deployment `dep-dc01upsipgvc738sa6e0` and backend `public-online-service-provider-api` deployment `dep-dc01upsipgvc738sa5g0` are both live from that commit. No deployment was triggered by this audit.
- Backend Render logs on 2026-11-20 show `SKIP_DATABASE_BOOTSTRAP=1` caused `pre_migrate.py`, Alembic upgrade, `seed.py`, and job snapshot import to skip. No production database migration, seed, snapshot import, or other database write was performed in this run.
- Render liveness logs show `/health` returning 200. `/readiness` and the DB-backed `/api/jobs/` endpoint were not called because they can connect to the production database, which remains prohibited. The live `/api/scholarships/` fetch returned the Render loading interstitial; API-level production verification is therefore incomplete.

### Public opportunity audit (2026-11-21)

- Live static jobs snapshot: 5 records, generated 2026-11-20T09:57:59Z. No published deadline before or on 2026-11-21 was found. The official SBI page currently lists six open notices: CRPD/SCO/2026-27/31 (10 Dec), /36 (3 Dec), /29 (25 Nov), /28 (25 Nov), /26 (23 Nov), and /27 (23 Nov). The current POSP snapshot contains /31, /36, /26, and /27 but omits the two still-open notices /29 and /28. SBI /30, whose official application last date was 16 Nov, is absent from the active snapshot. The SBI source is marked successful with four published items despite the two omissions; source completeness is not demonstrated.
- Job source health in the same snapshot shows 13 of 20 sources failed or degraded: NVS, Sainik Schools, DRDO-RAC, RRB, UPSC, MHA IB, TGPRB, India Post GDS, India Post Vacancies, ISRO, NCS, Infosys, and Accenture. These errors are not evidence of expiry; the affected opportunities must remain unverified until checked.
- Live static scholarship snapshot: 27 records, generated 2026-11-20T10:21:34.719517Z. All 27 have a 30 Nov student-application or renewal deadline; none is expired or due on 21 Nov. The official NSP page confirms Beedi/Cine/IOMC/LSDM Pre-Matric and Post-Matric student applications closed 31 Oct, Pre-Matric Scholarship for Students with Disabilities closed 31 Oct, and NMMS student applications closed 15 Nov. These closed schemes are absent from the active public snapshot. PR #253 is closed unmerged; the replacement scholarship-status fix was merged in PR #255 (`e014f50756ff59694a8a972ba768a8f648ba4ce4`; CI 43497910100 and E2E 43497910086 passed).
- NEC Merit Scholarship is explicitly renewal-only on the official NSP page. The backend catalog carries `application_scope=renewal_only`, while the checked-in frontend snapshot has a null scope; ensure the UI and fallback snapshot do not present a renewal deadline as a general first-time application.
- Scholarship source health records failures for AP JnanaBhumi (HTTPError), Social Justice (ConnectTimeout), and Tribal Affairs (SSLError), with six unverified records. These are not expiry evidence and must stay excluded from verified-open public counts until rechecked.
- The live sitemap contains 140 URLs, including 5 job details and 27 scholarship details; no closed Beedi/NMMS items were found in those active detail routes. Live robots.txt contains `User-agent: *`, `Allow: /`, and the sitemap URL. Render configuration sets `X-Robots-Tag: noindex, nofollow, noarchive` for private routes; live response-header verification remains outstanding.
- Expiry notification for this run: **No verified expired or deadline-today active listings found in the live static snapshots.** This does not certify the DB-backed jobs API or the full sync set as clean.

### Open PRs and blockers

- PR #268 head `fb1b1ed5a0e4f1021c1044c141fb5152d81a4e64`: CI 43952859017 and E2E 43952858934 passed, but it is 41 commits ahead / 10 behind current main and not mergeable. It contains a snapshot-only jobs API, DB-free `/health/rate-limit` and `/health/dependencies` probes, an SBI current-openings source change, and a regression test for /28 and /29. Rebase/reconcile it against current main and extend the SBI test to cover the newly listed /31 and /36 before considering merge.
- PR #270 was documentation-only at head `ef900bc9dbdd770e2aba5f2cf488f5b44b176ed6` (3 changed files, 3 ahead / 4 behind current main); its exact-head CI 44389263193 and E2E 44389263177 passed before this append. Revalidate checks and base immediately before any merge.
- PR #262 remains stale and must not be merged as-is. PR #232 still has insufficient missing-deadline behavior. PR #251's robots.txt Disallow approach conflicts with the current X-Robots-Tag noindex strategy. PR #252 and older overlapping PRs require fresh comparison before any action.
- No code change, merge, or new deployment was made in this audit. Keep the listing-correctness blocker open until the missing SBI notices, failed-source coverage, full API exposure, and scholarship UI scope are verified and fixed. Keep the Copilot AI provider refactor blocked pending explicit model/configuration review.
