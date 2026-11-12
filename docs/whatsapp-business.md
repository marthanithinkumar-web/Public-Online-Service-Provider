# WhatsApp Business integration

## Current website integration

The public website uses WhatsApp click-to-chat for the provider number `+91 9063403352`.

- A site-wide WhatsApp launcher is available on public/client pages.
- Service pages pre-fill the selected service when it can be resolved from the current route/catalog.
- Request detail pages provide a request-aware WhatsApp action that pre-fills the service name and request reference.
- The Contact page exposes WhatsApp alongside phone and email.
- Passwords, OTPs, PINs, CVV details and banking credentials must never be requested or sent over WhatsApp.

The click-to-chat number is centralized in `frontend/src/services/config.ts`, so a future WhatsApp Change Number migration only requires updating that configuration value.

## Meta WhatsApp Business Platform / Cloud API

The backend Cloud API transport remains disabled by default and no Meta access token or app secret is stored in the repository.

Production callback URL:

`https://public-online-service-provider-api.onrender.com/api/whatsapp/webhook`

Required environment variables:

- `WHATSAPP_CLOUD_API_ENABLED=1`
- `WHATSAPP_GRAPH_API_VERSION`
- `WHATSAPP_PHONE_NUMBER_ID`
- `WHATSAPP_ACCESS_TOKEN`
- `WHATSAPP_APP_SECRET`
- `WHATSAPP_VERIFY_TOKEN`
- `WHATSAPP_STATUS_TEMPLATE_NAME`
- `WHATSAPP_TEMPLATE_LANGUAGE` (defaults to `en`)

The status template sender expects body parameters in this order:

1. request reference
2. request status
3. secure request-tracking URL

The webhook verifies Meta's `hub.verify_token` challenge for setup and validates `X-Hub-Signature-256` on POST requests before accepting events. Verified inbound text is persisted in the existing support architecture so an admin can continue the conversation; it is not copied into email or operational alerts. The admin list endpoint redacts message bodies by default.

WhatsApp message rows have an explicit 90-day default retention policy, configurable with `WHATSAPP_MESSAGE_RETENTION_DAYS` from 30 to 3650 days. Cleanup is dry-run by default and is invoked through `python -m app.cli --whatsapp-messages`; permanent deletion additionally requires `--apply`. No recurring cleanup schedule is enabled by this local change, so production activation still requires an owner-approved maintenance schedule and verification.

## Stage 2: explicit client consent

Automated request-status messages are opt-in, not automatic for every client.

- `GET /api/whatsapp/config` exposes only whether automated status notifications are operational; it never exposes credentials.
- The request-detail page shows the WhatsApp status-update control only after the Cloud API transport and status template are configured.
- `POST /api/whatsapp/orders/<order_id>/preference` lets the authenticated owner explicitly enable or disable WhatsApp updates for that request.
- The preference is stored using the existing `contact_method=whatsapp` field and every change is recorded in request history for an auditable consent trail.
- Closed requests cannot newly opt in because they have no future status changes.
- Turning the preference off stops future WhatsApp status sends without affecting in-site or email updates.

## Production activation checklist

1. Create or select the Meta app and WhatsApp Business Account that owns the intended business number.
2. Add the production phone number and obtain the WhatsApp `phone_number_id`.
3. Create a long-lived production access token with only the permissions needed for WhatsApp messaging.
4. Configure the callback URL above and a private verification token in Meta, then store the same verification token in Render.
5. Store the Meta app secret in Render so webhook signatures can be validated.
6. Create and obtain approval for the request-status template with three body parameters: request reference, status and tracking link.
7. Add the production environment variables to the API service in Render while keeping `WHATSAPP_CLOUD_API_ENABLED=0`.
8. Verify the webhook challenge and signed webhook delivery.
9. Send a controlled template test to an opted-in test number.
10. Only after those checks succeed, change `WHATSAPP_CLOUD_API_ENABLED=1`.

A conversational inbound WhatsApp bot can be added later without changing the public click-to-chat implementation or the request-level consent model.

## 2026-11-04 implementation: automatic notifications, tracking, admin panel

Implemented without changing the existing consent model or click-to-chat:

- `backend/app/models/whatsapp_message.py` (`whatsapp_messages` table, migration
  `20261104_25`): outbound/inbound tracking, Meta message id, delivery
  status, retry count, and a unique `event_key` per business event.
- `backend/app/services/whatsapp_notify.py`: confirmation on order creation,
  status change on admin status update, document event for
  "Documents Required", and completion notification. All are best-effort,
  opt-in only (`contact_method=whatsapp`), deduped by event key, and
  never break order creation or status updates on failure.
- `backend/app/services/whatsapp.py`: template sending with bounded
  retries (transport/5xx/429 only), text sending for the 24-hour
  customer-service window, and webhook payload parsing.
- `backend/app/routes/whatsapp.py`: webhook now persists inbound
  messages (deduped by Meta message id or a bounded ID-less fingerprint), updates outbound delivery
  statuses, and hands matched inbound messages to the existing
  support-message thread (no separate WhatsApp-only chat, no message
  content in admin alerts). Admin-only endpoints:
  `GET /api/whatsapp/admin/status`, `GET /api/whatsapp/admin/messages`,
  `POST /api/whatsapp/admin/messages/<id>/retry`, and per-order
  `GET /api/whatsapp/orders/<id>/messages` for the owner or an admin.
- Frontend: `frontend/src/components/admin/WhatsAppManagement.tsx`,
  linked as `/admin/whatsapp`, shows connection/webhook/phone status,
  delivery statistics, failed messages with retry, and history.
  It never displays tokens or secrets. The backend admin list returns metadata
  without message bodies; per-order history remains restricted to the owner
  or an admin.

Still requires manual owner steps (see production activation checklist):
Meta app / WhatsApp Business Account / business phone number selection,
approved status template, long-lived token, and Render environment
variables. Until those are set, `WHATSAPP_CLOUD_API_ENABLED` stays `0`
and the sender stays inert; tests use mocked Meta responses.
