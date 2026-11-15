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
run #126 published snapshot `a1b9716`, which was fast-forwarded into local
`main`. The jobs snapshot digest marker matches the committed snapshot.

Production revalidation corrected one earlier finding: the official NSP page
now explicitly lists NMMS student applications through 2026-11-15 (and
verification through 2026-11-30). On 2026-11-15 at 13:17 IST, the API marked
NMMS `deadline_today`; that is current evidence, not a verification-date
mix-up. The scholarship should leave the public feed after its student
application deadline. The live feed currently has 27 scholarships (26
verified-open and one deadline-today) and three verified-open job records.
Across the 20 job sources, six report success, nine degraded, and five failed.
KVS and IBPS checks succeeded but yielded no published jobs; SEBI was blocked
with HTTP 530. The production source registry now points DRDO-RAC to the
official RAC site, but its latest source status is failed with two consecutive
failures. The parser successfully read the official page locally and returned
its expired notice, which is not published; production source connectivity or
runtime diagnostics still require owner-authorized logs.

The frontend build regenerated the sitemap to 172 URLs, matching the live
sitemap count. Two of the three live job records have indexable detail pages;
the third has a 237-character slug and is excluded by the SEO catalog's
200-character path guard. Production `robots.txt` allows crawlers to reach
routes and all 12 configured private routes return `noindex, nofollow,
noarchive`. The latest production smoke run failed because its robots assertion
incorrectly expected private routes to be disallowed; that contradictory
assertion has been removed and production smoke #116 passed. Browser E2E #470
exposed an obsolete sitemap-size threshold; the catalog-based correction was
committed in `00ccde8` and E2E #471 passed. A test-fixture isolation issue
found during the full-suite rerun was also corrected.

## Executive summary

The repository is a mature React/TypeScript + Flask/SQLAlchemy service, not an
MVP. It contains authentication and role checks, service/application flows,
fees and payments, uploads and object storage, admin/client dashboards,
notifications, official-opportunity feeds, SEO generation, backup tooling, CI,
and browser tests. Local backend tests, frontend typecheck/build, and the live
API readiness probe pass.

The largest verified gaps are external activation and incomplete source health:

- Of 20 production job sources, six report success, nine degraded, and five
  failed. KVS and IBPS reported successful checks with zero published notices;
  SEBI and DRDO-RAC report failures. The live job feed and sitemap were
  revalidated after the refresh.
- NMMS is currently deadline-today per the official NSP student-application
  row, not expired as the earlier snapshot indicated. The feed must remove it
  after 2026-11-15 and continue excluding expired listings.
- Render's checked-in configuration disables client AI and selects a model
  different from the requested `gemini-3.5-flash-lite`. Model availability and
  deployed credentials cannot be verified without a provider credential.
- The production WhatsApp configuration endpoint reports Cloud API disabled
  and status notifications unavailable. This is not a successful production
  messaging integration.
- Google Search Console coverage, Meta message delivery, AI provider calls,
  live payment transaction completion, and restore-drill activation require
  authorized external accounts or controlled transactions and are not proven
  by source code or readiness alone.

## Requirements assessment

The prompt has **12 top-level requirement areas**. Their verified status is:

| Area | Status | Evidence / remaining work |
|---|---|---|
| 1. Repository audit | Partial | Inspected repository structure, current history, 288 local/remote branch refs, 10 open PRs, core docs/configuration, tests, and live endpoints. Not every historical branch diff or commit was individually reviewed. |
| 2. Preserve previous requirements | Partial | Worktree was clean at start; the current main feature set and tests were retained. No stale branch was blindly merged. |
| 3. Platform features | Partial | Existing auth, client/admin workflows, orders, fees, uploads, receipts, notifications, and management functions have implementation and backend coverage. External live user journeys and all roles were not independently exercised in production. |
| 4. Jobs and scholarships | Partial | Scheduled refresh is configured for 07:45 IST; 20 sources are configured; backend/frontend filters, snapshot integrity, deadline, and freshness rules have regression coverage. Current production status is 6 successful, 9 degraded, 5 failed. KVS/IBPS succeeded with no published jobs; SEBI remains blocked with HTTP 530; the production DRDO-RAC registry points to the official RAC URL but reports failed with two consecutive failures. The parser reads the official RAC page locally and rejects its expired notice. The production API matched snapshot `a1b9716`; source health remains unresolved. The NSP official page confirms NMMS student applications through 2026-11-15; verify post-deadline removal. |
| 5. POSP AI | Incomplete | Existing in-client support chat and admin operations AI are present with grounded context and safe error handling. `render.yaml` sets `POSP_CLIENT_AI_ENABLED=false` and `POSP_AI_MODEL=gemini-2.5-flash`; requested settings are `true` and `gemini-3.5-flash-lite`. No provider key/model API check was performed, so operational status is unverified. |
| 6. WhatsApp Cloud API | Incomplete | Webhook verification/signature handling, inbound/outbound services, status updates, templates, consent, and admin monitoring are implemented and tested. Production `/api/whatsapp/config` reports disabled and notifications unavailable. |
| 7. SEO/indexing | Partial | Public metadata/canonicals/structured data, sitemap and robots generation, prerendering, and private-route `X-Robots-Tag` behavior are implemented. Production homepage, sitemap, and robots return HTTP 200; all 12 private routes return HTTP 200 with a noindex header. The build and production sitemap each contain 172 URLs. Only two of three live job records have prerendered detail URLs; the third's 237-character slug exceeds the SEO path guard. Google Search Console indexing status is inaccessible here. |
| 8. Security/reliability | Partial | Production startup rejects a missing/weak `SECRET_KEY`; auth/admin tests, input validation, upload limits, rate limiting, private storage, payment verification, backups, and readiness checks exist. Live readiness reported database, SMTP, S3, shared rate limits, and Razorpay checks ready. This is not a penetration test or restore drill. |
| 9. Testing/integration | Partial | Backend suite: 318 passed, 129 warnings; frontend typecheck/build passed. Production smoke #116, CI #1009, and authenticated browser E2E #471 passed. E2E #470's stale `>2000` URL assertion was corrected. Job refresh #126 passed and the production API matched its exact 3-job snapshot and 20-source registry. External AI, WhatsApp, real transaction/refund, and restore tests remain unverified. |
| 10. Git/merging | Partial | 288 branches and 10 open PRs were found. Changes were pushed in `a818b93` and `00ccde8`; job-refresh snapshot `a1b9716` was automatically pushed and fast-forwarded locally. Historical branch contents were not all reviewed; stale PRs were not merged. |
| 11. Deployment | Partial | Live health/readiness endpoints return HTTP 200, with all ten readiness checks true. Job refresh verified the production API against the exact committed snapshot hash. The RAC source registry is updated, but its latest health is failed. No authenticated Render control-plane view was available; AI and WhatsApp remain disabled. |
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
- Production frontend, API health, robots, sitemap, and private-route noindex
  header returned HTTP 200 during this audit.
- The current SEO build generated 172 canonical public URLs. Private pages are intentionally
  not blocked in `robots.txt`: crawlers must be able to read their `noindex`
  response headers. The production `/my-orders` response includes
  `X-Robots-Tag: noindex, nofollow, noarchive`.
- Of the three current SBI job records, two have prerendered detail pages. The
  third has a 237-character slug and is excluded by the SEO catalog's
  200-character filesystem-path guard; a safe route strategy is still needed
  before claiming complete job-detail SEO coverage.
- `Employment News All Jobs` is absent from the source search and the build
  includes a regression check to prevent its reintroduction.

## Broken or incomplete behavior observed

- **Priority-source health:** the latest production source endpoint reports
  six successes, nine degraded, and five failures across 20 sources. KVS and
  IBPS checks succeeded (six and 12 fetched, respectively) with no published
  jobs.
  SEBI is blocked with HTTP 530. The `drdo_rac` registry now uses
  `https://rac.gov.in/index.php?lang=en&id=0`, but its latest production status
  is failed with two consecutive failures. The parser successfully fetches
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
- **AI activation/configuration:** the checked-in Render blueprint explicitly
  disables client AI and has a different model. There is no evidence here of
  an accessible production Gemini key or a successful call to the requested
  model. Do not describe client AI as operational until this is verified.
- **WhatsApp activation:** production config says Cloud API is disabled. A
  source implementation and webhook tests do not establish Meta activation,
  verified webhook delivery, approved templates, or message delivery.
- **SEO validation:** the local build and production sitemap each report 172
  URLs, with the current deadline-today NMMS detail included. The live feed has
  three jobs but only two have prerendered detail pages because one slug is
  237 characters and exceeds the existing 200-character path guard. Do not
  increase the guard without checking filesystem and client-route behavior.
  Search Console coverage and indexing errors cannot be inspected without
  Search Console access.
- **History/branch review:** 288 branches exist, mostly historical feature/fix
  branches. The 10 open PRs were enumerated; only the latest source-freshness
  PR (#259) was selected for detailed integration because its changes directly
  address the verified live listing defect and its exact-head checks pass.

## Test/build results

- `python -m pytest -q backend/tests` from the repository root with
  `PYTHONPATH=backend`: **318 passed**, 129 warnings, 183.38s.
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
- Job refresh #126 passed; it published snapshot `a1b9716`, and the production
  API's jobs total, source count, and snapshot SHA matched the committed data.
- Initial frontend validation attempts before `npm ci` failed because the
  checkout had no installed frontend dependencies; the subsequent locked
  install and reruns succeeded.

## Security and external integration limits

- No credentials were copied into the report or queried from private
  configuration.
- Production readiness checks show the deployed DB, SMTP, storage, limiter, and
  Razorpay configuration are reachable. They do not prove a payment was
  captured/refunded or a backup was restored.
- AI and WhatsApp are intentionally classified as unverified/disabled based on
  their production-visible configuration. No Meta or model call was attempted.
- `robots.txt` is not an access-control mechanism; private APIs remain protected
  by authentication/authorization. The frontend noindex header only controls
  indexing behavior.

## Deployment and next work

1. Investigate DRDO-RAC's two consecutive production source failures using
   owner-authorized Render logs; the production endpoint confirms the corrected
   official RAC URL but hides the error cause. Do not bypass source controls.
2. Resolve the SEBI HTTP 530 block through an approved official source or
   owner-authorized network access; verify KVS and IBPS parsing and keep all
   unavailable sources fail-closed.
3. Check that the scholarship refresh removes NMMS after its 2026-11-15
   student-application deadline and that the production API and sitemap
   converge on the following refresh.
4. Configure and verify the requested Gemini model/API with an authorized key,
   or retain the disabled flag and disclose AI is unavailable.
5. Configure Meta WABA credentials, callback verification, phone/template
   settings, and consent; perform owner-authorized inbound/outbound delivery
   tests before enabling production messaging.
6. Inspect GSC coverage, validate canonical/noindex behavior for all private
   routes and pagination, resolve any reported indexing issues, and provide a
   safe indexable route for the current valid job notice whose slug exceeds the
   SEO path-length guard.
7. Perform owner-authorized end-to-end payment/refund, database backup/restore,
   and representative client/admin production journeys.

The job refresh workflow is configured for 02:15 UTC (07:45 IST), but the
latest scheduled run observed before this merge started at 08:55 UTC on
2026-11-14. Scheduled GitHub Actions timing is therefore not verified to meet
the requested refresh time; monitor future runs and use a more reliable
scheduler if this delay persists.
