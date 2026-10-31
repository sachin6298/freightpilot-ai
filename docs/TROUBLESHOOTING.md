# Troubleshooting Guide

## Frontend cannot reach backend
- Confirm FastAPI is running at the configured URL.
- Check `VITE_API_BASE_URL`; restart Vite after changing `.env.local`.
- Confirm backend CORS includes the exact frontend origin and scheme/port.
- Check browser console/network tab for the failed request and server logs for the matching request.

## PayPal button does not render
- Confirm `VITE_PAYPAL_CLIENT_ID` is the Sandbox client ID and it is not blank.
- Confirm SDK script parameters contain the expected sandbox client ID and supported currency.
- Check browser network/console errors; do not paste secret values into the browser to “test” them.
- Confirm app is using Sandbox accounts/environment, not mixing live and sandbox IDs.

## Create-order fails
- Confirm `PAYPAL_ENV=sandbox`, client ID/secret pair belongs to the same Sandbox REST app, and backend environment is loaded.
- Check server logs with secrets redacted.
- Make sure the quote exists and has a valid server-owned amount/currency.
- Call the endpoint through FastAPI `/docs` with a real quote ID.

## Buyer approved but payment shows pending
- Approval does not equal successful capture. Check backend capture endpoint and provider response.
- Query the saved provider order ID in Sandbox and reconcile the provider status.
- Do not manually force the local record to captured. Fix the status transition and test again.

## Webhook is rejected
- Confirm the configured webhook ID belongs to the same Sandbox app.
- Verify the request using PayPal's official signature-verification mechanism.
- Ensure the public endpoint is reachable over HTTPS and raw headers/body are handled as required by the SDK/API.
- Do not bypass signature verification to make the demo pass; disable optional webhook demo if necessary and still demonstrate server-side capture.

## AI summary is missing or wrong
- Confirm AI API key is only in backend environment and provider/model values are correct.
- Log request IDs and validation errors, but do not log secrets or unnecessary personal data.
- Ensure the prompt receives structured quote fields and risks, not only a vague user query.
- Add a deterministic fallback and show which method produced the summary.

## Python/package errors
- Activate the backend virtual environment.
- Reinstall from `requirements.txt`.
- Run `python -c "import fastapi; print(fastapi.__version__)"` to confirm the interpreter/package environment.
- Start from the directory expected by the documented module path, e.g., `uvicorn app.main:app --reload --port 8000` from `backend/`.

## Node/package errors
- Run `pwd`/`Get-Location` and confirm `package.json` exists in the current directory.
- Run `npm install` only in the folder that contains the relevant `package.json`.
- Use the Node.js version supported by the package configuration and inspect the actual error above the final npm summary.
