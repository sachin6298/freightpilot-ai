# Deployment Plan

## Deployment preference
Choose the simplest platform the team can reliably support. A single frontend host plus a separate FastAPI host is acceptable; keep the database managed if using PostgreSQL. Render is a reasonable option, but use any platform that provides persistent/managed data storage and HTTPS.

## Backend configuration
- Set Python build/start commands for the project structure.
- Configure environment variables in the hosting dashboard, not in repository files.
- Set `APP_ENV=production` and `DEMO_MODE=true` for the hackathon unless there is a deliberate alternative.
- Configure `FRONTEND_ORIGIN` to the exact deployed frontend origin.
- Use PostgreSQL for a hosted multi-instance service; a local SQLite file may not persist reliably across redeploys/instances.
- Configure PayPal Sandbox credentials and public HTTPS webhook endpoint if using webhooks.
- Configure health checks and inspect logs with secrets redacted.

## Frontend configuration
- Set `VITE_API_BASE_URL` to the deployed HTTPS backend URL.
- Set the PayPal Sandbox client ID and supported currency.
- Rebuild after changing Vite environment variables; these are embedded during build.

## Security/reliability smoke checks
- No secret values in compiled JavaScript or publicly visible repository history.
- CORS only permits the intended origin(s).
- API docs may be enabled for a judge-friendly demo; restrict operational/debug endpoints.
- API errors are sanitized.
- Seed/demo reset endpoint is disabled outside demo mode or protected.
- PayPal return route checks backend payment state.
- Webhook ID corresponds to the configured Sandbox app and signature verification works.

## Fallback strategy
Always keep a known-good local run path and record the exact commands in README. If the hosted payment callback or webhook configuration fails during recording, debug it rather than editing the UI to fake a completed payment. The recorded video must show the real Sandbox flow used by the project.
