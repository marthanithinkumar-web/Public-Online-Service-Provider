# POSP AI data handling

This note describes the context the backend may send to the explicitly configured AI provider. Provider use is controlled by `POSP_AI_ENABLED` and `POSP_AI_PROVIDER`; client support AI additionally requires `POSP_CLIENT_AI_ENABLED=true`. When client AI is disabled, customer support replies do not call an AI provider.

## Client support

When enabled, the backend sends the latest support message (at most 2,000 characters), up to four recent conversation messages (at most 320 characters each), and relevant POSP context. The latest message and history pass through the current sensitive-text redactor, which targets email addresses, Indian phone numbers, PAN patterns, and Aadhaar-labeled identifiers. Free-form identifiers or sensitive details outside those patterns can remain in text; customers should avoid including unnecessary personal information.

Relevant context is limited to at most five matching service summaries (name, category, a shortened description, fee fields and keywords); at most three of that user's recent orders (service and status only, without order code); and, only when asked about jobs or scholarships, at most three verified active listings of that type. Listing context contains public notice/application links, dates, eligibility/location summaries and source verification timestamps. No customer name, account email, user ID, phone number, address, payment credentials, or order code is intentionally included in the client prompt.

The assistant must hand uncertain POSP-specific answers to a human. Current jobs and scholarships are limited to verified active records. The public listing details sent to the provider can still be stale by the time the customer acts; users should confirm details at the official source.

## Admin operations assistant

Admin prompts may include aggregate readiness checks, counts of published, active, stale, expired, hidden or review-needed notices, source health and sync timestamps, scholarship source health, AI configuration/health state, and related operational findings. The operations context is built from system status and public listings; it does not intentionally include customer profiles, customer conversations, order records, payment details, or credentials. Admin AI should be used for operations questions, not pasted customer records.

## Logging and provider configuration

Provider failures are mapped to consistent safe errors. Logs should contain the error category only and must not contain provider keys, prompts, customer messages, or provider response bodies. The selected provider is explicit; a missing key or failed provider does not silently switch providers. Keep the client AI setting disabled until the organization has selected and configured a provider and reviewed its data handling terms.
