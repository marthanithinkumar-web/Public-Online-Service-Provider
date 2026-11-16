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
- Client and admin login now await the existing Render health warm-up before sending credentials, and display a connection status while the service is waking.
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
