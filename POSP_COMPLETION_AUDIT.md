# POSP Completion Audit

**Audit date:** 2026-11-15  
**Repository:** `marthanithinkumar-web/public-online-service-provider`  
**Starting branch:** `main` at `023a581ed5a88180d263cdf83ad10fd9b025b556`

This audit distinguishes code/test evidence from production behavior and from
external integrations that could not be verified without account credentials.
It is a point-in-time assessment; the final completion report records changes
made after this audit.

## Post-audit integration update

After recording the initial findings, exact-head-green PR #259
(`dccdfe4fae4037db685c55a4e50bdd072d8537ca`) was fast-forwarded into the local
`main`. It adds India-time/cutoff and source-freshness checks, corrects the
expired NMMS application deadline, adds a missing SBI security-officer notice,
and updates supporting tests and migration. Local targeted tests and the
frontend build/typecheck passed against this merged tree. This revision has not
yet been pushed/deployed at the time of this update. A follow-up SHA-256
comparison found that the new jobs snapshot had not been paired with its
deployment marker. The marker was corrected and a newline-normalized regression
test was added; the marker now matches the committed snapshot bytes.

## Executive summary

The repository is a mature React/TypeScript + Flask/SQLAlchemy service, not an
MVP. It contains authentication and role checks, service/application flows,
fees and payments, uploads and object storage, admin/client dashboards,
notifications, official-opportunity feeds, SEO generation, backup tooling, CI,
and browser tests. Local backend tests, frontend typecheck/build, and the live
API readiness probe pass.

The largest verified gaps are external activation and production data parity:

- The deployed opportunity feed returned 4 active jobs from 20 configured
  sources; the served sitemap still exposed the NMMS scholarship record that
  the current deadline reconciliation identifies as expired.
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
| 4. Jobs and scholarships | Partial | Scheduled refresh is configured for 07:45 IST; source registry has 20 entries; backend/frontend filters and stale/expired rules have regression coverage. Live feed/sitemap parity is stale, and complete current source-by-source verification is still needed. |
| 5. POSP AI | Incomplete | Existing in-client support chat and admin operations AI are present with grounded context and safe error handling. `render.yaml` sets `POSP_CLIENT_AI_ENABLED=false` and `POSP_AI_MODEL=gemini-2.5-flash`; requested settings are `true` and `gemini-3.5-flash-lite`. No provider key/model API check was performed, so operational status is unverified. |
| 6. WhatsApp Cloud API | Incomplete | Webhook verification/signature handling, inbound/outbound services, status updates, templates, consent, and admin monitoring are implemented and tested. Production `/api/whatsapp/config` reports disabled and notifications unavailable. |
| 7. SEO/indexing | Partial | Public metadata/canonicals/structured data, sitemap and robots generation, prerendering, and private-route `X-Robots-Tag` behavior are implemented. Production homepage, sitemap, robots, and `/my-orders` noindex header return HTTP 200. Production sitemap contains NMMS despite the expired-application finding; Search Console indexing status is inaccessible here. |
| 8. Security/reliability | Partial | Production startup rejects a missing/weak `SECRET_KEY`; auth/admin tests, input validation, upload limits, rate limiting, private storage, payment verification, backups, and readiness checks exist. Live readiness reported database, SMTP, S3, shared rate limits, and Razorpay checks ready. This is not a penetration test or restore drill. |
| 9. Testing/integration | Partial | Local backend suite: 295 passed; post-merge focused suite including snapshot-marker regression: 75 passed. Frontend typecheck and production build passed after installing locked dependencies. PR #259 has successful exact-head CI and authenticated browser E2E checks. Production integrations requiring credentials were not exercised. |
| 10. Git/merging | Partial | 288 branches and 10 open PRs found; verified PR #259 was fast-forwarded into local `main`. Historical branch contents were not all reviewed; stale PRs were not merged. Remote publication remains pending. |
| 11. Deployment | Partial | Live frontend/API endpoints respond; API readiness is `ready`. No authenticated Render control-plane view was available. Production feature flags and content still expose incomplete integration/data issues. |
| 12. Final destination | Incomplete | Work is not production-complete until the external AI/WhatsApp configuration and the remaining feed/source/deployment checks are verified. |

## Verified completed behavior

- Flask authentication, client/admin authorization, order/payment handling,
  configurable fee rules, support messages, refunds, and WhatsApp workflows
  have focused backend tests.
- Official-source job/scholarship validation, deadlines, filters, snapshots,
  and scheduled refresh are implemented with regression tests.
- The merged opportunity rules use declared timezone/cutoff fields and source
  freshness, keep invalid/expired items out of public feeds, and retain audit
  records. Local merged snapshots now contain five verified SBI notices and
  26 active scholarships; the expired NMMS application is not in the active set.
- The merged job JSON and backend SHA-256 deployment marker now match; the
  added regression test normalizes Windows line endings before comparing the
  committed snapshot digest.
- Frontend has dedicated service, jobs, scholarships, account, application,
  order, admin, and support views. Browser E2E coverage exists in CI.
- Production readiness returned HTTP 200 with all ten reported checks true:
  database, persistent document storage and connectivity, shared rate-limit
  storage and connectivity, SMTP delivery/connectivity, Razorpay live
  credentials, webhook configuration, and Razorpay connectivity.
- Production frontend, API health, robots, sitemap, and private-route noindex
  header returned HTTP 200 during this audit.
- The post-merge SEO build generated 173 canonical public URLs. Private pages are intentionally
  not blocked in `robots.txt`: crawlers must be able to read their `noindex`
  response headers. The production `/my-orders` response includes
  `X-Robots-Tag: noindex, nofollow, noarchive`.
- `Employment News All Jobs` is absent from the source search and the build
  includes a regression check to prevent its reintroduction.

## Broken or incomplete behavior observed

- **Opportunity freshness:** production API returned four active job records;
  the live sitemap still included `national-means-cum-merit-scholarship`.
  The current official-source reconciliation in PR #259 says NMMS applications
  closed on 2026-08-31; the later verification date is not an application
  extension. Local merged snapshots now remove NMMS from active publication;
  production still needs the correction and post-deploy parity verification.
- **SBI coverage:** production data had four SBI records. The local merged
  snapshot adds the currently verified Manager (Security)/Deputy Manager
  (Security) notice and related cutoff/source-freshness checks.
- **AI activation/configuration:** the checked-in Render blueprint explicitly
  disables client AI and has a different model. There is no evidence here of
  an accessible production Gemini key or a successful call to the requested
  model. Do not describe client AI as operational until this is verified.
- **WhatsApp activation:** production config says Cloud API is disabled. A
  source implementation and webhook tests do not establish Meta activation,
  verified webhook delivery, approved templates, or message delivery.
- **SEO validation:** the live sitemap and API opportunity data are not yet
  shown to be synchronized. Search Console coverage and indexing errors cannot
  be inspected without Search Console access.
- **History/branch review:** 288 branches exist, mostly historical feature/fix
  branches. The 10 open PRs were enumerated; only the latest source-freshness
  PR (#259) was selected for detailed integration because its changes directly
  address the verified live listing defect and its exact-head checks pass.

## Test/build results

- `python -m pytest -q backend/tests`: **295 passed**, 129 warnings, 200.14s.
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
- PR #259 exact head `dccdfe4fae4037db685c55a4e50bdd072d8537ca`: GitHub CI's
  operational safety, backend tests, frontend typecheck/build, and authenticated
  Chromium E2E checks all reported success.
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

1. Publish the locally merged main and confirm the production API, static data,
   frontend detail pages, and sitemap converge.
2. Resolve/verify all configured official sources, especially any failed or
   degraded checks; confirm notice/application URLs, accurate cutoffs, and no
   expired or unverified listings are public.
3. Configure and verify the requested Gemini model/API with an authorized key,
   or retain the disabled flag and disclose AI is unavailable.
4. Configure Meta WABA credentials, callback verification, phone/template
   settings, and consent; perform owner-authorized inbound/outbound delivery
   tests before enabling production messaging.
5. Inspect GSC coverage, validate canonical/noindex behavior for all private
   routes and pagination, and resolve any reported indexing issues.
6. Perform owner-authorized end-to-end payment/refund, database backup/restore,
   and representative client/admin production journeys.

The job refresh workflow is configured for 02:15 UTC (07:45 IST), but the
latest scheduled run observed before this merge started at 08:55 UTC on
2026-11-14. Scheduled GitHub Actions timing is therefore not verified to meet
the requested refresh time; monitor future runs and use a more reliable
scheduler if this delay persists.
