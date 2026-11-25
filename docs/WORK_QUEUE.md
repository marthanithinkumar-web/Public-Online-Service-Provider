# Public Online Service Provider — Active Work Queue

Last updated: 2026-08-31

## Completed production checkpoint

1. Completed: changed the homepage hero heading from **“Public Services, Made Simple”** to **“Public Services, Made Easier for You”**.
2. Completed: preserved the existing homepage menu because its Sign In/Register actions and service links are clearly visible and easy to use.
   - Keep the existing Jobs, Scholarships, MeeSeva, Certificates, and Schemes navigation.
   - Do not create a duplicate category/menu section.
   - Limit this instruction to the homepage; preserve the separate vertical client/account dashboard menu.
3. Completed: inspected and repaired the client dashboard **Explore Services** search bar.
   - Verify the actual root cause before editing.
   - Test live typing, partial words, substrings, case-insensitive matching, categories, tags/keywords, result links, empty/error/loading states, keyboard use, and mobile behavior.
   - Verify frontend-to-backend API communication and prevent slow, hanging, duplicated, or stale requests.
4. Completed: ran targeted frontend and backend tests for these changes.
5. Completed: verified the updated journeys on the deployed production website, not localhost only.

## Completed stopped checkpoint

6. Completed: Render backend deployment and database migration verification for the merged fee-transparency release.
   - Root cause found on 2026-08-26: the app factory queried the new fee columns before `flask db upgrade` could apply them, causing Render deploys to fail during startup.
   - Applied and verified the migration-safe bootstrap fix through the successful Blueprint deploy on 2026-08-26.
   - Confirmed `official_fee_status` and `official_fee_inr` are present in production.
   - Verified health, CORS, database connectivity, migrations, partial service search, and production fee displays.

## Active audit

7. In progress: audit every visible button, link, form, menu and navigation journey.
   - First confirmed gap: grievance/review forms exposed internal numeric IDs, and the grievance UI claimed the request was optional while its endpoint required one.
   - Replace typed internal IDs with choices from the signed-in client's own requests.
   - Allow an honest general-support grievance without a linked request, preserve ownership checks for linked requests, and use non-sequential unique grievance references.
   - Offer reviews only for completed requests owned by the signed-in client.
   - Next confirmed gap: the application wizard displayed editable contact fields even though the secure backend correctly uses the client's account profile. Make the source of truth explicit and direct edits through Account Settings so changes are never silently ignored.
   - Confirmed upload gap: client screens and route-level validation allow 10 MB documents, while the global server default allowed only 5 MB. Align local, documented, and Render limits with the visible 10 MB rule.
   - Confirmed public-navigation gap: category pages read a URL parameter that none of the explicit category routes provides, leaving all five menu destinations stuck in loading. Map each real route to its catalog query and add timeout/retry handling.
   - Confirmed smartphone-header gap from production screenshots: at phone and mobile “desktop site” widths, all Login/Register/navigation destinations are hidden behind a small icon-only control. Keep the complete drawer, add always-visible account shortcuts, improve touch targets/grouping, protect contact text from overflow, and verify both viewport modes.
   - User refinement: preserve one shared homepage across laptop and smartphone; do not create a separate mobile homepage. Replace the disliked shortcut row with a compact search icon plus off-canvas menu, and make the existing homepage scale cleanly at phone widths.

## Completed public homepage refresh

8. Completed: implemented the approved search-first homepage proposal without creating a separate mobile homepage.
   - Kept Client Login, Create Account, and Admin Login easy to find.
   - Moved live service search and Popular Searches into the hero.
   - Added database-backed Popular Services, clear categories, a three-step request journey, safety warnings, private-provider disclosure, and fee transparency.
   - Added Railway Ticket Booking Assistance as a searchable database-backed service.
   - Applied a one-time ₹30 current assistance-fee migration while preserving future per-service admin editing and historical order fee snapshots.

## Preserved fee rule

- The private assistance fee is admin-configurable per service; ₹30 is only a starting value.
- The admin may change it to ₹50, ₹100, or another valid non-negative value.
- Existing requests retain the fee recorded when they were submitted; later requests use the updated fee.
- Government/official fees and private assistance fees must always remain clearly separated.

## Completed Option A whole-site checkpoint (local)

9. Completed: extended the approved Option A search-first design across the public, client, and admin experiences.
   - Added a clear Track My Request path and retained visible Client Login, Create Account, and Admin Login access.
   - Added responsive vertical client and admin workspace navigation, with Delete Account kept discreet inside the protected client account menu.
   - Reworked public information, service-detail, contact, footer, application, grievance, review, and admin-management screens around the shared blue/teal design system.
   - Added Railway Ticket Booking Assistance requirements and explicit warnings that clients must complete OTP and payment themselves on the official platform.
   - Added production database pooling, Gunicorn concurrency settings, query indexes, and responsive/loading improvements.

10. Completed: added an admin-dashboard-only **Update fee across website** control.
   - The admin can replace the current assistance fee on every service with one confirmed value.
   - The action requires an authenticated active admin, a confirmation checkbox, a final confirmation prompt, and server-side amount validation.
   - Existing submitted requests and receipts retain their original fee snapshot.
   - Public homepage, search results, popular services, service details, and future requests load the database-backed value instead of a hard-coded ₹30.
   - Important bulk fee changes are stored in the admin audit log and shown in Activity & Reports.

11. Verified locally on 2026-08-26:
   - Frontend TypeScript check and production Vite build passed.
   - All 34 backend tests passed, including client isolation and client → admin → status → client notification workflow coverage.
   - Full migrations `20260824_01` through `20260826_07` and the 91-service seed completed successfully on a clean database.
   - These latest changes still require GitHub push, Render deployment, and production-browser verification before this checkpoint can be called live.

12. Completed: safe client request withdrawal and account-deletion protection.
   - Clients can cancel only their own request and only while its status is New, Submitted, Pending, or Documents Required.
   - Requests already In Progress, Completed, Rejected, or otherwise beyond the safe cancellation window cannot be cancelled directly; the client is directed to provider support/grievances.
   - Every cancellation adds a status-history entry, timestamp, and client notification.
   - Account deletion is blocked while active requests exist and lists the affected request references with links to resolve them.
   - Password verification, two-step UI confirmation, ownership enforcement, and session invalidation remain required for deletion.

## Continuation rule

After the items above are complete and tested, continue the existing full improvement queue one item at a time. Preserve working code, fix root causes, verify security/privacy isolation, and do not describe the website as 100% complete until the full production and end-to-end test suite passes.

## Launch-readiness continuation (2026-08-26)

13. Completed locally: expanded the database-backed catalog from 91 to 122 active services.
   - Added citizen-document, student-admission, employment, welfare, health, business/licence, utility/civic and transport assistance.
   - Railway Ticket Booking Assistance remains an ordinary searchable service.
   - Added tailored, privacy-safe application fields and repeated warnings that clients complete OTP and payment authorization themselves.

14. Completed locally: persisted the admin-controlled website-wide assistance fee.
   - Newly seeded or newly created services inherit the last admin-set global assistance fee.
   - Existing submitted requests retain their original fee snapshot.
   - Added migration `20260826_08` and tests for post-change service creation and catalog seeding.

15. Completed locally: finished private grievance tracking.
   - Clients can list and track only their own grievances, including general support grievances.
   - Admin responses, validated statuses, history, client notifications and audit records are connected.
   - Removed duplicate legacy grievance/review routes so trailing-slash variants use the same authorization checks.
   - Removed the unused destructive admin client-deletion endpoint; suspension/reactivation remains available.

16. Completed locally: strengthened authentication and public-review privacy.
   - Registration now enforces the same eight-character password minimum shown in the UI.
   - Public reviews omit client names, contact details, request IDs and internal order IDs.
   - Client request/grievance timelines no longer expose staff email addresses.
   - The homepage shows database-backed service/category counts and moderated verified-client reviews when available.

17. Verified locally for this batch:
   - All 40 backend tests passed.
   - TypeScript checking and the production Vite build passed.
   - Clean migrations through `20260826_09` and an idempotent 122-service seed passed.
   - A simulated ₹65 global fee remained ₹65 for newly seeded services.

18. Still required before public-launch sign-off:
   - Full authenticated browser E2E runs using isolated client/admin test accounts.
   - Production migration/deployment verification for this batch.
   - Confirm persistent S3-compatible document storage, shared rate-limit storage, SMTP delivery and database backups in Render.
   - Complete keyboard/mobile/browser/accessibility, slow-network, load/concurrency and recovery testing.

## Zero-fee and deployment-readiness checkpoint (2026-08-27)

19. Completed locally: protected free-service pricing and service availability.
   - An admin may set one service's private assistance fee to ₹0.
   - The confirmed website-wide fee action also accepts ₹0 and persists it for newly created services.
   - Existing submitted requests retain their original fee snapshot.
   - Official Document PDF Access Assistance remains an ordinary catalog service and can be disabled or re-enabled through Admin → Services & Fees.
   - An explicit disabled state survives application bootstrap and production catalog reseeding.

20. Completed locally: strengthened deployment health and readiness reporting.
   - Added a database-backed `/health` endpoint and configured Render to use it.
   - Superseded by owner instruction: administrator email-code verification has been removed and is no longer a readiness control.
   - Verified 49 backend tests, frontend TypeScript/build, clean migrations through `20260826_10`, a 123-service seed, and disable-state persistence across reseeding.

21. Still required before claiming 100% public-launch readiness:
   - Publish and verify this checkpoint on Render.
   - Complete isolated authenticated client/admin browser E2E tests.
   - Confirm production S3-compatible storage, SMTP, Redis-backed rate limits and database backup/restore.
   - Do not restore administrator email-code verification unless the owner explicitly requests it.
   - Complete keyboard, screen-reader, mobile/browser, slow-network, load, concurrency, cold-start and recovery testing.

## Encrypted backup checkpoint (2026-08-31)

22. Implemented in the repository: independent encrypted database backup and guarded recovery tooling.
   - A daily GitHub Actions workflow creates a PostgreSQL custom archive, encrypts it with AES-256 before upload, verifies checksum/decryption/archive structure, and uploads only encrypted material to a separate private B2 bucket.
   - Exact B2 object-version cleanup keeps 14 daily backup sets without hidden versions silently consuming the free allowance.
   - Restore verification is non-mutating by default. A real restore refuses the production Neon branch host and requires an exact expected temporary host plus explicit confirmation.
   - Still required: add the seven GitHub Actions secrets, complete the first green manual backup, and complete one restore drill on a temporary Neon branch before marking database recovery ready.

## Admin application archive checkpoint (2026-08-31)

23. Completed locally: added a safe admin-only archive for closed applications.
   - Only completed, rejected, or cancelled applications can be archived; active applications remain visible in the operational queue.
   - The default admin list and dashboard pipeline exclude archived applications, with dedicated Archived and All filters plus restore controls.
   - Archiving never deletes the request, documents, status history, grievances, reviews, payment/fee records, reports, or audit evidence.
   - Client APIs, the client dashboard, and the client's complete application history are unchanged and do not expose admin filing state.
   - Archive and restore actions require an active administrator account and create admin audit-log records.
   - Still required: publish only after the current Render deployment is stable, run the migration, and complete production admin/client isolation checks.

## 2026-11-07 — POSP expired scholarship production blocker (active)

- Owner authorized the GitHub repository as the normal code-writing path. This supersedes the earlier blocked-write constraint for branch/commit/PR work; it does not authorize automatic merge or deployment.
- Latest verified main at branch creation: `f1391efac69f721b14f3956cb1b85d84f3496770`.
- Cross-chat continuity retrieval was completed before repository inspection. Current open PRs/issues and workflows were inspected; no existing branch already contained this focused NSP parser correction.
- Confirmed official NSP page states Beedi/Cine/IOMC/LSDM Pre-Matric student applications closed on 31-10-2026; 15-11-2026 is defective/institute verification. The adjacent PM YASASVI Top Class Education in Schools scheme has its own student-application deadline 15-11-2026. Official source: https://scholarships.gov.in/All-Scholarships.
- PR #252: https://github.com/marthanithinkumar-web/Public-Online-Service-Provider/pull/252
- Branch: `fix/verified-scholarship-application-status-20261107`.
- Latest branch head at this handoff: `f996d99883832af03f1b2b14c53ffdaf234c83bf`.
- Code changes: NSP parser recognizes explicit student-application closure/open labels, scopes date association to the relevant card, parses labeled dates even when the card dates share one text row, records source evidence/timezone/check timestamp, and separates closed/expired scholarship records into `closed_items` rather than active `items`.
- Regression tests added for the Beedi/PM YASASVI neighboring-card bug, combined-row dates, verification-date separation, closed record audit retention, and closed/cancelled active-eligibility rejection.
- Browser E2E workflow pinned to Ubuntu 24.04 because the previous `ubuntu-latest` runner resolved to Ubuntu 26.04, which Playwright 1.55.0 could not install on. The failed earlier E2E run stopped before test execution due to that runner incompatibility.
- Exact-head CI and E2E for `f996d99883832af03f1b2b14c53ffdaf234c83bf` were in progress when this entry was written: CI run 42324692738; authenticated browser E2E run 42324692752. Frontend typecheck/build and operational safety had succeeded; backend tests and Chromium install were still running.
- No merge, deployment, production data mutation, customer/request/payment change, or real notification occurred.
- Remaining blocker: verify all current active jobs and scholarships against official sources; fix same-advertisement job supersession and stale carry-forward; add item-level freshness/status evidence and safe deadline cutoff handling; enforce across API/search/frontend/AI/SEO/sitemap; add admin sync/failure reporting; complete regression coverage; obtain green exact-head CI and production API/UI/sitemap verification. Do not declare the listing set clean.



## Verified scholarship publication and expiry checkpoint (2026-11-13)

- Reconciled current main at `5292d8b79b9c61c2ccbe76b5a0643638db759459` with current Render deployments. The POSP static site and API are both live on this commit. Render API startup logs confirm the current job snapshot imported 5 active published jobs across 20 configured sources.
- Current official NSP page: https://scholarships.gov.in/All-Scholarships (checked 2026-11-13 01:26 IST). It lists student application closure on 31-10-2026 for Beedi/Cine/IOMC/LSDM Pre-Matric, Beedi/Cine/IOMC/LSDM Post-Matric, and Pre-Matric Scholarship for Students with Disabilities. Their institute verification remains open until 15-11-2026; this is not an application deadline. The current deployed scholarship snapshot incorrectly included Beedi Pre-Matric as active with a 30-11-2026 deadline, a false date taken from a neighbouring card. The current snapshot also omitted some genuinely open NSP cards and had not separated evidence/status fields.
- The active fix branch applies card-scoped NSP parsing, separate student-application versus verification dates, explicit official status evidence, Asia/Kolkata timezone, 36-hour freshness, deadline-today warning state, closed-item audit preservation, unverified-item review retention, API/catalog filtering, frontend status labels, and SEO/sitemap exclusion. It also corrects the checked-in snapshot to 25 evidence-backed active NSP items and 3 closed audit records pending the next full daily discovery refresh.
- The scholarship refresh workflow validates that public items have fresh official evidence and student-application deadlines, that closed records never overlap the active set, and that production matches the refreshed snapshot. It no longer requires unverified Telangana ePASS records to be publicly listed.
- PR #253 is still open/unmerged and based on the older main commit. Its CI failed (backend tests and browser E2E), and its review identified that closed_items were not preserved by subsequent refreshes. The current branch includes the durable closed_items preservation fix and regression coverage; do not merge PR #253 as-is.
- Current job audit: the deployed verified snapshot contains 5 published jobs. One RBI Part-Time Bank's Medical Consultant notice is due today, 13-11-2026 at 17:00 IST (official RBI page: https://rbi.org.in/Scripts/Bs_viewcontent.aspx?Id=5192); it is not expired at 01:26 IST. Four SBI notices have future official deadlines (16, 23 and 25 November 2026). No verified expired job was found in the current five-item snapshot. Source coverage remains imperfect: several job sources report failed/degraded fetches, so this is not a full nationwide audit.
- Job cutoff/source-freshness follow-up is tracked in GitHub issue #256: https://github.com/marthanithinkumar-web/Public-Online-Service-Provider/issues/256.
- Remaining job cutoff blocker: jobs currently carry date-only deadlines and the API/frontend do not enforce a published cutoff time. The RBI item could remain visible after 17:00 IST on its last date. Next dependency-safe work is to add explicit deadline time/timezone to the job snapshot, parser, model/importer, API eligibility, frontend and regression tests; do not hide the RBI item before 17:00 IST and do not claim its cutoff is enforced yet.
- Production verification remains incomplete for the scholarship API/UI and sitemap. Render deployment metadata is confirmed, but the live scholarship API response and rendered detail/sitemap output have not yet been independently fetched after this change. Do not claim the scholarship fix is live until a green PR is merged under the approved workflow and the live API, listing, detail route, AI context and sitemap are checked.


## 2026-11-14 — POSP expired-opportunity production blocker (active; append-only)

- Cross-chat continuity retrieval was completed before this run. Current main, open PRs/issues, recent snapshot commits, exact-head CI, current Render deployment metadata, the official NSP page, and the current public job snapshot were reconciled before edits.
- Current main: `69c318bdde2d020a1d4805f1411b840ca430128f`. Render confirms both `pospindia` and `public-online-service-provider-api` are live on this commit. The deployed main scholarship snapshot still publishes Beedi Pre-Matric as active with a false `2026-11-30` deadline; official NSP checked 2026-11-14 01:12 IST says student applications closed `2026-10-31`. The `2026-11-15` date is defective/institute verification and `2026-11-30` is DNO/SNO/MNO verification, not a student application deadline.
- Official NSP also confirms Beedi Post-Matric and Pre-Matric Scholarship for Students with Disabilities closed on 2026-10-31. Those two were not in the current main public snapshot; the fix branch preserves all three as closed audit records.
- PR #255: https://github.com/marthanithinkumar-web/Public-Online-Service-Provider/pull/255. Branch `fix/verified-scholarship-status-20261113`. The branch now includes main snapshot commits `3a690114f583bcce5188e1f193f0efa24b5caff3` and `69c318bdde2d020a1d4805f1411b840ca430128f` through merge commit `53fef430e83bacf2226e023428d19c7d39d414da`; no main changes were discarded.
- Scholarship fix: current branch snapshot contains 24 evidence-backed active NSP records, 3 closed audit records, and 1 unverified record. PM-USP CSSS is held unverified because the official card says `Scheme : NOT YET OPENED` despite a future date. NEC Merit Scholarship is explicitly marked renewal-only and the frontend status/action labels say so. Public frontend snapshot contains active records only. The parser, API catalog, frontend, SEO and scheduled snapshot workflow fail closed on closed/unverified/stale items.
- Production smoke was corrected: it no longer requires Telangana ePASS items to be public when their application status is not verified, and it checks Beedi/CSSS exclusion, item-level freshness, official evidence, and renewal-only scope without expecting internal source-health data in the public API.
- The exact-head CI and authenticated browser E2E from the preceding code head `f81e8a85693ab4edf5c11c682875da5be1717416` passed (CI run `43496823510`; E2E run `43496823494`). Subsequent smoke-workflow and renewal-evidence commits require a fresh exact-head CI/E2E run; do not rely on the earlier runs for the final head.
- Job audit from current main snapshot `frontend/public/data/jobs.json` generated `2026-11-13T09:27:47Z`: 5 published items, 20 configured sources (6 success, 5 failed, 9 degraded). RBI Part-Time Bank's Medical Consultant has official deadline 2026-11-13 17:00 IST and remains `published` in the raw snapshot on 2026-11-14. API, frontend and SEO use India-date filters and should exclude it after local midnight, but exact cutoff-time enforcement is not implemented and the raw static JSON remains stale until the next daily job refresh (07:45 IST). Four SBI notices remain future-dated (16, 23, 23 and 25 November). Wipro returned 6,892 fetched and 0 published; the prior unavailable Wipro job is no longer in the snapshot.
- Job source coverage is not complete; direct live API/UI/sitemap retrieval was unavailable in this run. Render deployment metadata proves the deployed commit, not the response content. Keep issue #256 open for exact cutoff/timezone, source freshness and all-surface enforcement. Keep issue #257 open for admin sync health/review/retry reporting.
- No merge, deployment, production data mutation, customer/request/payment change, or real notification occurred in this run. The production blocker remains open until the current PR is merged under the approved workflow, deployed, and the live API, listing/detail UI, search, AI/notifications, sitemap and source sync are verified.


## 2026-11-14 02:07 IST — POSP expired-job and scholarship audit (append-only)

### Continuity and deployed state
- Cross-chat retrieval returned no additional matching conversation records in this run; canonical GitHub and Render state were inspected directly.
- Current inspected main: cdb754e34a995daa8f3019cd4973269e8d68edc8 (Refresh verified official job snapshot [skip ci]).
- Scholarship eligibility work from PR #255 was merged as e014f50756ff59694a8a972ba768a8f648ba4ce4. Render API and frontend both subsequently deployed cdb754e34a995daa8f3019cd4973269e8d68edc8 successfully. Render service health checks returned HTTP 200. This proves deployment, not full live-feed correctness.
- PR #253 remains open but is superseded by the merged/deployed PR #255 scholarship closure implementation. Do not treat #253 as the active fix path.
- Live Render API/UI/sitemap payload retrieval was not independently completed in this run; do not claim a full production content audit.

### Scholarship source audit
- Official NSP page checked at 2026-11-14 02:07 IST: https://scholarships.gov.in/All-Scholarships
- NSP explicitly reports Beedi Pre-Matric and Post-Matric student applications closed on 31-10-2026; their 15-11-2026 dates are verification windows, not student application deadlines. Pre-Matric Scholarship for Students with Disabilities is also marked student-application closed on 31-10-2026.
- Main backend scholarship snapshot: 24 public active items, 3 closed audit records, 1 unverified review record; Beedi is absent from active items. The public projection contains 24 active items and excludes internal audit records.
- New official change: PM-USP CSSS now says Scheme Open from 22-10-2026 and Student Application Open till 30-11-2026. The checked-in backend snapshot still holds it as unverified based on older NOT YET OPENED evidence. A regression test was added on this branch so the next approved scholarship refresh must promote it only from the current official evidence.
- National Means Cum Merit Scholarship has student applications open until 15-11-2026 (tomorrow relative to this audit); no scholarship application deadline was due today.

### Job source audit and confirmed stale record
- Current checked-in public job snapshot SHA d913ff192725ec8cce641e3e5cb187474d4328e9, generated 2026-11-13T20:11:28Z (2026-11-14 01:41:28 IST), contains 5 published items from 20 source records. Source health: 5 success, 4 failed, 11 degraded.
- Confirmed expired record still present as status=published in the raw public snapshot: RBI “Engagement of Part-Time Bank’s Medical Consultants (BMC) … Thiruvananthapuram”, deadline 2026-11-13. Prior official notice evidence recorded in issue #256 states the application cutoff was 13-11-2026 17:00 IST. The RBI portal returned a CAPTCHA in this run, so its content could not be freshly re-read; the known official deadline is nevertheless before the current India date. Raw snapshot publication is a confirmed leak. Current API/frontend/SEO code applies India-date filtering, but the actual live API/UI response could not be independently fetched.
- Official SBI current-openings page checked at 02:07 IST: https://sbi.bank.in/web/careers/current-openings. It confirms fixed-term SCO registration extended through 16-11-2026; Risk Specialist and Product & Research roles through 23-11-2026; Assistant Manager Engineer (Fire) through 25-11-2026. The same official page also lists Manager (Security)/Deputy Manager through 25-11-2026, which is absent from the five-item POSP snapshot; source coverage is incomplete.
- Root cause of the expired RBI raw-snapshot leak: backend/app/jobs/snapshot.py used now.date() (UTC) while backend/app/jobs/priority_sources.py and two parsers in backend/app/jobs/sources.py used date.today(). At 20:11 UTC on 13 November, India was already on 14 November, so the 13 November deadline was retained in the raw snapshot.

### Current fix branch and remaining blocker
- Branch: fix/posp-india-local-job-expiry-20261114, based on current main cdb754e34a995daa8f3019cd4973269e8d68edc8.
- Changes on branch: shared Asia/Kolkata date helper; India-local expiry in priority/source parsers and snapshot carry-forward; fail-closed job model open state; India-local frontend date/status text; prevent empty snapshots replacing still-current prior records; job refresh workflow restricted to main and validates source-registry parity plus explicit non-expired deadlines; regression tests for India-midnight expiry and the newly opened PM-USP CSSS.
- Exact-cutoff time/timezone is still not persisted in the job model or enforced at the published time-of-day boundary. Issue #256 remains open for that broader work, admin sync metrics, and full API/search/AI/sitemap regression coverage. Issue #257 remains open for source-failure/admin review operations.
- No merge or deployment of the current fix branch has occurred. Exact-head CI and production smoke are pending. Keep the production blocker open; do not claim the active jobs/scholarships set is clean until live API, UI, sitemap, AI/notifications, source completeness and official-source evidence are verified.


## 2026-11-15 — POSP expired-opportunity continuity (append-only)

- Cross-chat preflight retrieved the latest POSP handoff: PR #255 was actually merged at 2026-11-13T20:11:15Z as merge commit `e014f50756ff59694a8a972ba768a8f648ba4ce4`; earlier handoff text saying it was still open was stale. PR #253 is closed unmerged and superseded. PR #252 and #232 remain old open PRs and are not safe merge candidates.
- Latest inspected main is `023a581ed5a88180d263cdf83ad10fd9b025b556` (2026-11-14T08:59:34Z job snapshot refresh). Main contains the merged scholarship eligibility code.
- Live official NSP page checked 2026-11-15 00:35 IST: https://scholarships.gov.in/All-Scholarships. Beedi Pre-Matric and Post-Matric student applications, and Pre-Matric Scholarship for Students with Disabilities, are closed on 2026-10-31; later verification dates are not student application deadlines. National Means Cum Merit Scholarship has student applications open till 2026-11-15, with no cutoff time shown on the page; it is therefore a deadline-today warning, not verified-open after an unknown cutoff. PM-USP CSSS is still marked NOT YET OPENED. NEC Merit Scholarship is renewal-only.
- Live public scholarship snapshot `https://pospindia.onrender.com/data/scholarships.json` is still generated at `2026-11-12T19:56:04+00:00`, with 24 items and `verified_open_count=24`, `deadline_today_count=0`. Beedi is absent, but the National Means Cum Merit record still says `application_status=open` with deadline `2026-11-15`; its count is stale for the current date. The live sitemap has 125 URLs (3 job details, 24 scholarship details) and still includes the National Means Cum Merit detail URL on its deadline date. It does not include Beedi detail URLs.
- Live public job snapshot `https://pospindia.onrender.com/data/jobs.json` was generated `2026-11-14T08:55:47Z`: 4 published SBI notices with last dates 16, 23, 23 and 25 November. The source report shows 20 configured sources, 6 successful and 14 failed/degraded; no expired job was found among the 4 published records, but nationwide coverage is incomplete.
- Direct production API retrieval is currently unavailable to the external fetcher. Production scholarship smoke run 43584332820 failed after repeated API timeouts; do not claim live API verification. Production public smoke run 43578323077 separately fails because deployed robots.txt lacks private-route exclusions (tracked by the existing robots PR/SEO work).
- Root cause found in the scholarship refresh workflow: `backend/app/scholarships/snapshot.py` wrote a literal backslash-`n` after the JSON document, so the scheduled refresh generated the snapshot but the next `json.loads` failed with `JSONDecodeError: Extra data` (run 43579730307, line 1333). This prevented the refreshed 27-record official discovery result from being serialized/published. A real-newline fix and JSON roundtrip regression test were added to the existing work branch below; the 27-record result is not yet a committed or deployed production snapshot.
- Continuing branch `fix/posp-deadline-cutoff-freshness-20261114` rather than creating a duplicate branch. It carries job cutoff/timezone, source freshness, API/frontend/AI/SEO filters, scholarship status refresh and tests. The separate branch `fix/job-deadline-cutoff-and-india-date-20261114` remains untouched for reconciliation; it diverged and must not be overwritten.
- Issues #256 (job exact cutoff/source freshness) and #257 (scholarship admin sync/review/retry dashboard) remain open. No merge, deployment, customer/request/payment mutation, or real notification occurred in this run. Keep the production blocker open until exact-head CI, approved deployment, live API/UI/search/AI/sitemap and complete official-source audit are verified.

## 2026-11-15 01:03 IST — POSP expiry audit and deadline-cutoff follow-through (append-only)

### Cross-chat and canonical preflight
- Prior-conversation retrieval was attempted; no additional transcript records were returned in this run. Reconciled from this canonical work queue, current GitHub PRs/issues/CI, live POSP endpoints, and official issuing portals.
- Current main inspected at \`023a581ed5a88180d263cdf83ad10fd9b025b556\`. Its one-commit delta from the PR merge base updates only \`frontend/public/data/jobs.json\` and \`backend/app/jobs/verified_snapshot.sha256\`.
- PR #255 is merged and its scholarship closure rules are on main. PR #253 is closed unmerged/superseded. PR #252 remains an older stale open PR; do not merge it. PR #259 is the active combined deadline/freshness fix; immediately before this handoff its branch head was \`26daf761b84614ef29c39d52f2aad4c9ac741325\`, 55 commits ahead / 1 behind main and mergeable. It must include the latest main snapshot/checksum commit before final CI/merge.

### Production audit — checked 15 November 2026, approximately 01:03 IST
- POSP API health endpoint returned healthy. Live \`/api/jobs/?limit=100\` returned 4 records; live \`/api/scholarships/\` returned 23 records.
- Live jobs snapshot was generated \`2026-11-14T08:55:47Z\`. All four published deadlines are in the future: SBI fixed-term SCO 16 Nov; Risk Specialist 23 Nov; Product & Research 23 Nov; Assistant Manager Engineer (Fire) 25 Nov. No verified expired job deadline was found among these four. However, the SBI source-health roll-up is only 6 success / 5 failed / 9 degraded across 20 sources, so this is not a complete nationwide job audit.
- Official SBI current-openings page presently confirms the fixed-term SCO notice (last date 16 Nov) and Product & Research notice (last date 23 Nov). The Risk Specialist 2026-27/27 official PDF states an application window 2–23 Nov, but that notice is absent from the current-openings page and its application portal fetch timed out; treat the live POSP Risk Specialist record as unverified pending portal/source confirmation, not as proven expired. The live POSP Assistant Manager Engineer (Fire) record has no individual official notice/application URL, is absent from the current SBI openings page, and its detail page still publicly offers assisted application; treat it as unverified and exclude from verified-open feeds. These two unverified records are still present in the live API/static feed and Fire is in the sitemap.
- Live scholarship static feed was generated \`2026-11-12T19:56:04Z\` and contains 24 records with stale top-level counts (24 verified-open, 0 deadline-today). The live scholarship API returns 23 and omits National Means Cum Merit Scholarship (NMMS). Official NSP page \`https://scholarships.gov.in/All-Scholarships\` lists 31 cards: 27 student-application open, 3 closed, and 1 not yet opened. Beedi Pre-Matric, Beedi Post-Matric, and Pre-Matric Scholarship for Students with Disabilities are closed for student applications on 31 Oct 2026; the later verification dates are not student deadlines. Those closed records are absent from the live static feed, API, and sitemap; no Beedi URL appears in the live sitemap, and the old Beedi route no longer resolves to that scheme.
- NMMS has an official student application last date of 15 Nov 2026 with no published cutoff time. It must be labelled \`Deadline today—check official portal\`, not verified-open and not apply-now. The live static feed still says open/counts it verified-open; the API excludes it; the live sitemap still contains its detail URL. This is a production consistency defect, not a past-deadline claim.
- Live sitemap contains 139 URLs, including 3 job-detail URLs and 24 scholarship-detail URLs; NMMS is present and Beedi is absent. The NMMS detail route resolves, but the extracted page text did not independently confirm its status label/source-link presentation.
- Current official NSP snapshot branch evidence covers 27 open, 3 closed, and 1 not-yet-open/unverified card; one of the 27 is renewal-only (NEC). Three currently open schemes missing from the live main feed are included in PR #259's refreshed catalog. Source evidence for the branch catalog was checked within the 36-hour freshness window.

### PR #259 changes made during this run
- \`backend/app/jobs/sync.py\`: flush new rows before adding database IDs to the seen set, preventing the cleanup pass from immediately demoting newly inserted jobs to needs_review.
- \`backend/tests/test_job_filter_contract.py\`: commit the source/item freshness fixture before the request runs in a new app context.
- \`backend/app/jobs/sources.py\`: rewrite explicit cutoff parsing so date-first dotted dates such as \`13.11.2099 at 17:00 hrs IST\` yield the cutoff.
- \`backend/app/routes/ai_operations.py\`: build AI job context from the same public freshness query and deadline eligibility used by the API; pass status label, cutoff/timezone, source check time and can_apply. Scholarship AI context now carries application status/scope and does not present closed/unverified or renewal-only records as new-applicant opportunities.
- \`backend/tests/test_ai_operations.py\`: add regression coverage for stale/expired/cutoff-passed job exclusion, deadline-today warning, and scholarship renewal-only scope.
- \`frontend/scripts/seo-catalog.mjs\` and \`frontend/scripts/verify-active-listing-rules.mjs\`: normalize deadline-today scholarships before sitemap eligibility and assert the explicit deadline-today status.
- Backend and frontend scholarship snapshots in the PR branch now mark NMMS \`deadline_today\`, with 26 verified-open and 1 deadline-today (27 public active records); the 3 closed and 1 unverified records remain outside the public active feed.
- \`e2e/tests/full-navigation-audit.spec.cjs\`: use the job title link for detail navigation and assert no assisted-application link for a deadline-today notice without a verified cutoff.

### Checks and blockers
- On prior exact PR head \`e00043061a08388d389952292526855b48ca9dd2\`, CI run 43633346626 passed; backend reported 307 passed and frontend typecheck/build passed. Authenticated browser E2E run 43633346611 failed only because it expected the obsolete link text \`View Details & Apply\`; the UI correctly rendered the new no-assistance \`View notice details\` state. The E2E selector/expectation was updated.
- Intermediate CI/E2E runs for later commits were cancelled by subsequent branch updates. No completed exact-head CI/E2E result has yet been confirmed for the latest branch head or the final main-integrated merge tree.
- No merge or deployment occurred in this run. Production still has the unverified Fire and Risk records and the NMMS static/API/sitemap inconsistency. The full job-source audit is incomplete because 14 of 20 job sources are failed/degraded. Admin sync metrics/review UI remains open under issue #257; the separate client notification service currently sends request-status/support notifications, not job-alert notifications.
- Next safe steps: integrate main commit \`023a581ed5a88180d263cdf83ad10fd9b025b556\` (jobs snapshot plus checksum) into PR #259 without overwriting its branch work; run exact-head CI and authenticated E2E; resolve any failures; merge only when current and green; deploy only through the approved Render workflow; run the official-source sync and verify live API, static feeds, UI/detail pages, sitemap, AI context and admin metrics. Keep this blocker open until all active jobs and scholarships are audited and all public surfaces are verified.



## 2026-11-15 — POSP exact-head CI repair checkpoint (append-only)

- Reconciled current PR #259 and its recorded branch head `0503264109224d8e8c47f01f027c3cac62d58896` against main `023a581ed5a88180d263cdf83ad10fd9b025b556`. The branch was 57 commits ahead / 0 behind at the PR body checkpoint; after this follow-up test-only commit it is 66 commits ahead / 0 behind. The merge base remains current main.
- Exact-head CI run `43634634136`: operational script safety passed; frontend typecheck/build passed; backend tests failed with 1 failure / 308 passed. The failure is `test_ai_job_context_uses_public_freshness_and_cutoff_eligibility` in `backend/tests/test_ai_operations.py`, raising Flask `RuntimeError: Working outside of application context` while setting up JobSource fixtures.
- Authenticated browser E2E run `43634634070` was cancelled during the 13th of 22 tests; it is not a pass.
- Follow-up branch commit `6a52e4b63cd66229bd239f46e95668da503744ad` changes that test to use `client.application.test_request_context('/')` for a request-bound application context. This is a proposed test-harness correction only; it is not considered verified until the test passes on this exact commit.
- No exact-head CI/E2E run was returned for commit `6a52e4b63cd66229bd239f46e95668da503744ad` at the time of this checkpoint. Do not merge PR #259 or deploy based on the earlier run.
- Issues #256 (exact job cutoffs/source freshness) and #257 (authenticated scholarship sync health/review/retry) remain open. The full official-source audit and production API/UI/search/AI/notification/sitemap verification remain release blockers.
- Next actions: obtain fresh exact-head CI and authenticated E2E on `6a52e4b63cd66229bd239f46e95668da503744ad`; inspect and fix any remaining failure; update PR #259's stale verification summary; only then merge under the approved workflow and verify Render production content. Preserve all previous work-queue entries and continue daily expiry/deadline-today reporting.


## 2026-11-15 — POSP official-source reconciliation and expired NMMS correction

- Checked the live official National Scholarship Portal page `https://scholarships.gov.in/All-Scholarships` on 2026-11-15. The current page lists National Means Cum Merit Scholarship student applications open only until `31-08-2026`; its later verification dates are 15-09-2026 / 30-09-2026. The prior production snapshot and PR #259 branch snapshot incorrectly carried `2026-11-15` as the student deadline, apparently confusing a downstream verification date with the application deadline.
- Corrected PR #259 branch data: backend scholarship snapshot commit `d6e9c4d23a6e23e6b2f86bb31e64f52b76174945` moves NMMS out of active `items` into `closed_items`, records the official 2026-08-31 student deadline and `deadline_passed` closure reason, and preserves source evidence/check timestamp. Frontend public snapshot commit `65ad8f56172d7f75de32e777d6fd2048d8cbb212` removes NMMS from public items. The PR branch public scholarship count is now 26, verified-open 26, deadline-today 0; backend closed audit count is 4.
- Added regression test `test_nsp_expired_student_application_deadline_is_moved_to_closed_audit` in commit `70eeb890bf14d8a6e69df76dfddbce1261026d60`. It verifies that an NSP card with a past student-application deadline but later verification dates cannot remain public and is retained in the closed audit queue.
- Checked official SBI Current Openings `https://sbi.bank.in/web/careers/Current-openings` on 2026-11-15. Five current notices are listed: CRPD/SCO/2026-27/30 (fixed-term, deadline 2026-11-16), /26 (Product & Research, 2026-11-23), /27 (Risk Specialist, 2026-11-23), /28 (Manager Security / Deputy Manager Security, 2026-11-25), and /29 (Assistant Manager Engineer—Fire, 2026-11-25). The live branch job snapshot contains /30, /26, /27 and /29; /28 is still missing. Its official advertisement is available at `https://sbi.bank.in/documents/77530/57941334/03112026_1_ADV_Security%2BOfficer.pdf/69e017fe-5e1c-6312-c285-8855f9882102?t=1793713497818`. The official notice directs applicants to the SBI Current Openings page for the online application link. Do not invent a direct application URL; resolve and add this listing through the approved source/parser workflow.
- Render read-only deployment inspection confirms both production services still run main commit `023a581ed5a88180d263cdf83ad10fd9b025b556`; latest frontend and API deploys are `live`. This is deployment metadata only. The web retrieval tool could not fetch the live API scholarship query, static scholarship JSON, or sitemap, so production content parity is not verified.
- These snapshot/test commits are branch-only and have not been verified by fresh exact-head CI/E2E. The previous exact-head CI `43634634136` failed (1 failed, 308 passed); E2E `43634634070` was cancelled. Do not merge/deploy until fresh exact-head CI and E2E pass.
- Issues #256 and #257 remain open. The full job-source audit, SBI /28 ingestion, admin sync metrics/review/retry, and live API/UI/search/AI/notification/sitemap verification remain release blockers.


## 2026-11-15 — SBI Manager Security listing added to verified branch snapshot

- Added the official SBI Manager (Security) / Deputy Manager (Security) notice, advertisement `CRPD/SCO/2026-27/28`, to `frontend/public/data/jobs.json` in commit `a255e8d9817768edd7ee591ac8c3c5ef70259fcd`.
- Record uses the official SBI notice PDF `https://sbi.bank.in/documents/77530/57941334/03112026_1_ADV_Security%2BOfficer.pdf/69e017fe-5e1c-6312-c285-8855f9882102?t=1793713497818`, official registration portal `https://ibpsreg.ibps.in/sbirscooct26/`, registration dates 04–25 Nov 2026, deadline 2026-11-25, 60 vacancies, and qualifications/experience taken from the official advertisement. Application portal and dates were cross-checked against the registration portal's how-to-apply page and the SBI notice. This closes the known fifth-current-SBI-opening omission in the branch snapshot; the main/production snapshot remains unchanged until merge/deploy.
- Public job snapshot item count is now 5 (previously 4). The record's content hash and ID are calculated using the repository's `item_hash` and `_serialize_item` rules. The existing SBI source health metadata remains at its last successful automated check (2026-11-14 08:55:47Z); manual official-source verification does not falsely claim a new automated source sync.
- The parser regression test for this exact SBI advertisement already exists in `backend/tests/test_priority_job_sources.py`; the snapshot addition still requires the latest branch CI, importer validation, and live production verification.


## 2026-11-15 — SBI Fire notice and application URL verified

- Corrected the existing SBI Assistant Manager – Engineer (Fire), advertisement `CRPD/SCO/2026-27/29`, snapshot record in commit `0cd1d9a235077bf9f0bdded6d92fe8e86767f268`.
- Replaced the generic SBI careers listing as its notice with the official advertisement PDF: `https://sbi.bank.in/documents/77530/57941334/04112026_FINAL%2BDRAFT%2BADVERTISEMENT%2BCRPD-SCO_29_ENGINEER.pdf/4d1be5a0-727d-61b5-1ea4-85570f437345?t=1793788834905`. Added the official application portal `https://ibpsreg.ibps.in/sbiameoct26/`, application start 2026-11-04, 17 vacancies, age 21–40 as on 2026-10-31, and the qualification alternatives from the official notice.
- The branch job snapshot now contains all five current SBI notices with individual notice/application URLs: /30, /26, /27, /28 and /29. The two previously incomplete /28 and /29 records now have official PDF and application URLs. Main/production remains unchanged until PR merge/deploy.


## 2026-11-15 — Latest E2E and backend regression failures corrected for rerun

- The authenticated E2E run `43689233588` failed before tests executed because `e2e/tests/full-navigation-audit.spec.cjs:128` contained an invalid escaped regex `/\\\\/scholarships\\\\//`. Corrected the route assertion to the valid `/\\/scholarships\\//` in commit `773ce801f7cb0af8bbd7f0993b7b8f957ee6d91f`.
- CI run `43689233632` completed frontend typecheck/build and operational-script safety successfully, but backend tests failed 1 / 314. The new NSP expired-deadline regression invoked `refresh_snapshot(strict=True)`, which intentionally rejects a one-card fixture because strict production refresh requires at least five official listings. Changed this focused test to `strict=False` in commit `151511ef1ea81d57f1de1127498f22ca0417a194`; the test continues to assert that the expired 2026-08-31 NMMS student deadline is removed from active items and retained as closed.
- These are test-harness fixes, not proof of completion. Fresh exact-head CI and authenticated E2E must pass after the latest branch changes. No merge or deploy is authorized until that verification succeeds.


## 2026-11-15 — Second E2E syntax failure fixed

- The authenticated E2E run on head `6c39f4649575d6c65de051f05a9d8d36f71ec988` passed setup and frontend/backend startup but failed during Playwright test parsing. The first scholarship route assertion had been corrected, but two additional assertions at lines 139 and 142 still contained invalid double-escaped regular-expression delimiters.
- Replaced those remaining regex assertions with Playwright URL predicates: scholarship detail paths must start with `/scholarships/`, and the assisted-application route must equal `/services/scholarship-application-assistance` and include the `scholarship` query parameter. Commit: `abf5244cd0802b162aeaf4e4724a10b17439ebb4`.
- Checked the full E2E spec for any remaining adjacent double-backslash sequences; none were found. This is still awaiting a fresh exact-head E2E run.
- Backend CI for the same earlier head was still running when this note was written. The new regression fixture was separately corrected to avoid invoking the unrelated strict minimum-five-listings gate; it still requires exact-head backend test success.


## 2026-11-15 — NSP expiry test made deterministic/offline

- Inspection of `source_enrichment.py` showed `refresh_snapshot()` performs optional official-page enrichment, which makes an unrelated network request. The new expiry regression does not test enrichment and should not depend on NSP availability.
- Updated `test_nsp_expired_student_application_deadline_is_moved_to_closed_audit` to monkeypatch `app.scholarships.snapshot.enrich_scholarships` to identity, keeping the test focused on expiry classification and deterministic/offline.
- Commit: `e4c83480e08264bd69aa73ef4eaed347e5551ebc`. Fresh exact-head CI is required; previous in-progress test results are not proof.

## 2026-11-16 — POSP fee, login and Copilot ZIP integration

- P0: Fix scholarship fee propagation across all scholarship service/category variants. The server now uses the persisted scholarship fee setting when creating new scholarship orders; existing orders retain their stored fee. Payment guard and client payment breakdown cover all variants.
- P0: Display the configured homepage assistance fee, refresh scholarship fee values on public service cards and request pages, disable caching for the public fee endpoints, and reload the admin catalog after fee changes.
- P1: Fix the client/admin login warm-up race, show an accessible secure-server connection status, and cache allowlisted API CORS preflight responses for 600 seconds to reduce repeated OPTIONS round-trips.
- P1: Apply location and qualification filters in the live jobs API fallback, synchronize job filter state with the URL, and cap search length.
- P1: Make the current Render backend startup sequence database-safe when its existing SKIP_DATABASE_BOOTSTRAP=1 flag is set. The pre-migrate, Alembic, seed, and snapshot importer commands now exit before database work; a subprocess test uses an isolated SQLite path. Do not remove this guard or change the existing production DB/Key Value settings.
- CI migration verification explicitly sets POSP_ALLOW_DATABASE_MIGRATIONS=1 only for the isolated SQLite migration-chain job. Render does not set this opt-in, so production startup continues to skip migrations.
- Copilot ZIP reconciliation: nested SEBI parser changes already landed in PR #261; package-lock changes already exist on main. Safe UI/filter/privacy changes are carried forward in this integration branch. Do not import the ZIP's invalid/unverified AI model default or Render setting that enables client AI; reconcile AI changes with open PRs #216/#226/#227/#235 first. Ignore generated assets, local DBs/caches/uploads and line-ending-only rewrites.
- New branch: fix/posp-fees-home-auth-zip-integration-20261116. Exact-head CI/E2E and PR are pending. No merge/deploy has occurred.
- Keep the official-source expired jobs/scholarships audit and PR #253 closure verification as independent open blockers; this fee/login PR does not close them.

### Final-head verification rerun — 2026-11-16
- First CI at c12531c passed backend tests, frontend typecheck/build and operational script safety; browser E2E failed on duplicate accessible labels. Selectors were corrected and category-only scholarship fee coverage was added after that run.
- Replacement integration branch: fix/posp-fees-home-auth-zip-integration-verified-20261116 (forked from code head 0d6f5ac). Fresh PR #265 will carry final exact-head checks. PR #264 is superseded and should be closed after #265 is open.
- Do not merge/deploy until all required checks pass on the final head.

- E2E follow-up: 26 tests passed on the prior head; one service-search test matched the header link rather than the input. Selector corrected to #service-search input[type=search]; final-head browser run required.

## P0 — Render production database startup hard guard (2026-11-16)
- First rolling deploy after PR #265 included a legacy instance that ran pre-migration/Alembic startup and imported 3 job snapshot records into the production DB. The logs show DB revision 20261114_26 and no recorded Running upgrade line; seed writes cannot be ruled out. No direct DB inspection or rollback was attempted. Treat this as a disclosed incident; never claim the no-production-DB-touch rule was fully maintained for that rollout.
- The subsequent deploy on current code logged skips for pre-migration, Alembic, seed and snapshot import. New branch fix/render-no-db-startup-hard-guard-20261116 adds unconditional Render-environment protection, even if migration opt-in is present. CI migration validation remains isolated SQLite-only.
- Do not connect to or alter the production DB to inspect or reverse the imported snapshot records. Preserve the incident note and require the hard-guard PR to pass CI before the next deployment.


## Permanent AI upgrade register — 24 November 2026

The ₹0 constraint applies to client and admin AI, including diagnostics. Free allowances on billable accounts are insufficient. Never activate billing, recharge or paid failover. Keep credentials server-side. Development and verification use fixtures and isolated databases. Production verification must avoid application database access.

| Requirement | Status at this change |
| --- | --- |
| Existing provider interface, client consent, bounded retries, safe handoff and verified listing context | Previously shipped |
| Built-in client knowledge and admin findings, local production spend guard | Implemented in this change; pending release verification |
| Groq GPT-OSS 20B/120B, Gemini multimodal, Cloudflare Workers AI and strictly free OpenRouter adapters | Adapters and synthetic mock coverage implemented; account verification and live comparison pending |
| Client/admin routing by task, language, latency and quotas; circuit recovery, caching, duplicate suppression, streaming and token accounting | Fixed public FAQ routing, bounded cache, cooldowns, duplicate suppression and per-process counts implemented; streaming and shared accounting pending |
| English, Hindi and Telugu assistance, continuity, personalized eligibility, official evidence, documents and image support | Partial; multilingual fee labels and directory navigation available locally |
| Admin provider controls, consumption, quotas, latency, failures, fallback history and cache metrics | Pending |
| Provider benchmarks and production enablement | Pending; do not call external providers during verification without confirmed hard billing limits |
| ZIP, WhatsApp, login, fees, verified filters and source sync, SEO, security, responsive UI and release work | Retain preceding queue and original acceptance criteria |

### Customer opt-in release verification

PR #276 introduced local production routing, public FAQ provider candidates and the free-tier spending guard. The customer opt-in release checks confirmed fees in three languages, unknown fees, conversation continuity, application guidance, requests for staff, payment uncertainty and empty verified listings through synthetic inputs. The readiness endpoint reports the configured opt-in flag independently of the probe results. Per-message consent is still required. Live external provider benchmarking, account-wide quota reporting, streaming inference, image/document processing and dashboard configuration remain open.

### Phase 4 provider diagnostics

FAQ traffic and administrator benchmarks share one atomic request reservation per provider per process, including failed attempts. The dashboard shows remaining daily process allowance, failures and recent response latency. Provider-reported tokens and attempts missing usage metadata are tracked locally. Provider account limits, streaming, multimodal processing and editable role settings remain open. Preserve the existing non-AI queue above.

Fixed public FAQs now answer after the support privacy and enablement checks, before account history and catalog retrieval. Privacy guidance is available in English, Hindi and Telugu.

SEO review of PR #251: its source robots change is overwritten by generate-seo.mjs and conflicts with verify-robots-rules.mjs. Retain crawl access for private-route noindex headers. Leave #251 open for reconciliation.

### Client notice reader

Opt-in support includes a local reader for UTF-8 notices and PNGs in browsers that implement text detection. It extracts source lines about dates, fees, eligibility and documents in English, Hindi and Telugu. Extracted content stays in transient component state. Unsupported image recognition provides a text-file fallback. PDF interpretation, authenticated free-provider benchmarks, full streaming, global settings and cross-worker quota accounting remain pending.

### Phase 4 streaming diagnostics

The admin dashboard can stream a fixed Groq fee benchmark in each supported language using the client or admin model. Diagnostics share the FAQ budget and cooldown. Test partial streams with fixtures. Live evaluations require confirmed hard-free accounts. General chat streaming, shared quota accounting, editable provider settings and verified external quality rankings remain pending alongside the earlier non-AI queue.

Local support filters explicit region searches before taking the first three verified results. It distinguishes confirmed official fees from assistance fees, and requests for an admin trigger handoff. DB-free release probes include official fee and admin handoff.
