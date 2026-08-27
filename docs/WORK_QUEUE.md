# Public Online Service Provider — Active Work Queue

Last updated: 2026-08-26

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
   - Confirm persistent S3-compatible document storage, shared rate-limit storage, SMTP delivery, admin 2FA and database backups in Render.
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
   - Admin 2FA is no longer reported ready unless both the feature flag and SMTP delivery are configured.
   - Verified 49 backend tests, frontend TypeScript/build, clean migrations through `20260826_10`, a 123-service seed, and disable-state persistence across reseeding.

21. Still required before claiming 100% public-launch readiness:
   - Publish and verify this checkpoint on Render.
   - Complete isolated authenticated client/admin browser E2E tests.
   - Confirm production S3-compatible storage, SMTP, Redis-backed rate limits, admin 2FA, and database backup/restore.
   - Complete keyboard, screen-reader, mobile/browser, slow-network, load, concurrency, cold-start and recovery testing.
