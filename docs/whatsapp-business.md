# WhatsApp Business integration

## Current website integration

The public website uses WhatsApp click-to-chat for the provider number `+91 9063403352`.

- A site-wide WhatsApp launcher is available on public/client pages.
- Service pages pre-fill the selected service when it can be resolved from the current route/catalog.
- Request detail pages provide a request-aware WhatsApp action that pre-fills the service name and request reference.
- The Contact page exposes WhatsApp alongside phone and email.
- Passwords, OTPs, PINs, CVV details and banking credentials must never be requested or sent over WhatsApp.

The click-to-chat number is centralized in `frontend/src/services/config.ts`, so a future WhatsApp Change Number migration only requires updating that configuration value.

## Future Meta WhatsApp Business Platform / Cloud API

The backend is prepared but deliberately disabled by default. No Meta access token or app secret is stored in the repository.

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

Only requests that explicitly record `contact_method=whatsapp` are eligible for automated WhatsApp status delivery. This prevents enabling the Cloud API later from messaging every existing client without an explicit WhatsApp preference.

The webhook verifies Meta's `hub.verify_token` challenge for setup and validates `X-Hub-Signature-256` on POST requests before accepting events. The current receiver intentionally does not persist or log inbound message content; it only acknowledges verified events and records aggregate event counts in application logs. A conversational bot/inbound workflow can be added later without changing the public click-to-chat implementation.
