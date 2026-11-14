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

