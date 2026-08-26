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

## Preserved fee rule

- The private assistance fee is admin-configurable per service; ₹30 is only a starting value.
- The admin may change it to ₹50, ₹100, or another valid non-negative value.
- Existing requests retain the fee recorded when they were submitted; later requests use the updated fee.
- Government/official fees and private assistance fees must always remain clearly separated.

## Continuation rule

After the items above are complete and tested, continue the existing full improvement queue one item at a time. Preserve working code, fix root causes, verify security/privacy isolation, and do not describe the website as 100% complete until the full production and end-to-end test suite passes.
