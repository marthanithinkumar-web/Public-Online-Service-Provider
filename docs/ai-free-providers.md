# POSP AI free-provider policy

Production support uses local facts while external accounts are unverified. No customer prompt is accepted by the provider evaluation endpoint. An authenticated administrator can evaluate a fixed synthetic fee question in English, Hindi or Telugu with POST /api/admin/ai/support-check. Supply benchmark_provider, role and language. Confirm the provider-side plan refuses billable requests and disables auto-recharge before marking an account verified. A key or an advertised free allowance alone does not establish this.

| Provider | Backend credential | Official account page | Permitted benchmark |
| --- | --- | --- | --- |
| Groq | GROQ_API_KEY | https://console.groq.com/keys | openai/gpt-oss-20b for client, openai/gpt-oss-120b for admin |
| Gemini | GEMINI_API_KEY | https://aistudio.google.com/apikey | gemini-3.5-flash-lite on an eligible unbilled project |
| Cloudflare | CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID | https://dash.cloudflare.com/profile/api-tokens | Workers Free account only |
| OpenRouter | OPENROUTER_API_KEY | https://openrouter.ai/settings/keys | google/gemma-4-26b-a4b-it:free, zero input/output price caps |

The optional server settings POSP_GROQ_FREE_ONLY_VERIFIED, POSP_GEMINI_FREE_ONLY_VERIFIED, POSP_CLOUDFLARE_FREE_ONLY_VERIFIED and POSP_OPENROUTER_FREE_ONLY_VERIFIED default to false. Never set them for a paid account. Confirm model availability and terms in the deployment region before each evaluation. Never paste keys in GitHub, frontend code or support chat.

A public GET to /api/admin/ai/local-readiness checks synthetic local fee answers and reports whether the local provider is selected. It performs no authentication lookup, database query or external inference. All dashboard and benchmark operations require admin access.

Client and admin public FAQ routing sends only fixed prompts; personal messages never become provider input in this path. Set POSP_CLIENT_AI_PRIORITY and POSP_ADMIN_AI_PRIORITY to comma-separated provider names. Current-process counters reset daily UTC, requests are capped at 25 per provider per worker, and failures open a two-minute cooldown. These local bounds cannot verify account-wide free quotas. Streaming, multimodal support and account-wide administration remain in WORK_QUEUE.md.

Admin benchmarks consume the same process allowance as FAQ requests. Refresh AI Operations to see remaining attempts, failures and the last 32 outcomes across providers. A cache hit consumes no provider request. The allowance resets at midnight UTC or process restart.

The process reports only total tokens returned by the provider. Failed requests and responses without valid usage metadata are counted separately as attempts without usage data. Usage is attributed to the UTC day the request started.

The support notice reader uses browser file APIs and the browser's optional native text detector for PNGs. It sends no files or excerpts to POSP or its AI adapters. Text matching extracts original lines, without verifying the issuer, interpreting legal eligibility or confirming deadlines.

AI Operations offers a streaming Groq benchmark for a fixed example in English, Hindi or Telugu. The admin-only endpoint accepts role and language. Free-account verification, daily reservations and cooldowns apply. Stopping a benchmark may still consume its reserved attempt. Incomplete output is discarded by the dashboard. No provider key or customer message is accepted by this endpoint.

AI Operations supports per-role ordering and disabling on a running instance. An empty order selects local-only behavior. All workers reserve from one 25-attempt daily UTC allowance per provider, including benchmarks. State is a private atomic JSON file under the instance temporary directory. A replacement instance starts fresh. Set POSP_CLIENT_AI_PRIORITY and POSP_ADMIN_AI_PRIORITY for deployment defaults. Runtime controls cannot override credentials, model allowlists or free-account verification.

For client messages, Accept application/x-ndjson requests streaming only for opted-in exact public FAQ topics in local mode. The server selects a fixed prompt and never interpolates customer text. Clients discard partial text on reset and render the saved reply on done. Other messages retain the JSON response contract.
