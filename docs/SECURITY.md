# Security controls and remaining work

## Implemented in this release

- Production configuration fails fast unless authentication is mandatory, demo mode and automatic schema creation are disabled, PostgreSQL is configured, HTTPS origins are set, Redis-backed rate limiting is enabled, and a strong JWT secret is supplied. Production also requires configured transactional email, SMS, PayPal and private S3-compatible storage credentials.
- JWTs use issuer, expiry, issue time, token ID and token-type claims; access-token lifetime is limited by configuration. Passwords use Argon2.
- Role/ownership checks were added to seller/admin analytics, marketplace seller operations, quote/counter-offer operations, shipment access, settlement listing and payment operations. Public role registration cannot create an administrator.
- Email verification stores only a token hash. Phone OTPs are hashed, bound to a unique registered E.164 number, short-lived, one-time and attempt-limited. SMS login requests do not disclose whether a phone number belongs to an account. Delivery providers are explicit and do not echo verification secrets in API responses.
- Document uploads are streamed with a hard size limit, extension/MIME allowlisting and file-signature checks. Metadata is persistent, files are private, download authorization is enforced, and downloads require a clean malware scan. Production document bytes use an S3-compatible bucket.
- Security response headers, exact-HTTPS production CORS allowlists (wildcards rejected), generic client error messages, secret-safe provider exception logging and Redis-backed production rate limits are installed. The readiness probe verifies both PostgreSQL and Redis in production.
- Gemini credentials are sent in an API header rather than a URL query parameter. Prompt context treats supplied shipment/quote text as untrusted.
- PayPal create/capture is server-side, amount/currency are compared with internal snapshots, duplicate webhook event IDs are tracked, capture beneficiary assignment requires an explicitly associated verified seller, and refunds require admin execution.
- Production migrations are performed by Alembic during Render pre-deploy, not `create_all` at application startup.

## Automated checks

- The backend regression suite is run in CI.
- The CI job runs the full Alembic migration chain against a fresh database, separately from ORM-created test fixtures.
- The project includes an automated Python compile check and a clean Vite production build check in CI.

## Mandatory operational controls

- Use provider-managed secret stores. Rotate leaked credentials and never commit `.env`, logs, database dumps or private files.
- Configure a healthy ClamAV daemon. Files stay quarantined while scanning is missing or unhealthy.
- Restrict object storage to private access; use least-privilege keys and encryption.
- Configure backups, point-in-time recovery where available, and run restore drills.
- Monitor authentication failures, rate-limit blocks, admin changes, shipment transitions, document access, payment transitions and webhook processing.
- Add an external security assessment before handling real customers or payments.

## Known limitations requiring product/provider work

- Google sign-in verifies the provider-signed ID token against Google's published signing keys, issuer, audience, expiry and nonce. Apple web sign-in exchanges the one-time authorization code using a short-lived ES256 client secret held server-side, then verifies Apple's signed ID token. Provider identities are persisted in `oauth_identities`; OAuth-created accounts start as buyers.
- Access tokens are still held by the existing browser client in localStorage; a future auth redesign should use a carefully implemented HttpOnly cookie/refresh-token architecture with CSRF protection. Avoid introducing permissive CORS or wildcard cookie domains.
- Google/Apple sign-in still requires the user's own provider-console setup and credentials before it is enabled. Phone OTP delivery in production requires a configured Twilio sender and destination-country approval.
- Carrier APIs and carrier webhooks need provider-specific integrations and contracts. Manual tracking status changes are restricted in production; no live tracking source is fabricated.
- Full seller payout/disbursement, escrow, dispute, partial-refund and buyer refund-request approval workflows are not implemented. The internal settlement ledger must not be represented as a real payout.
- Notifications beyond email/OTP delivery require a queue/worker, retry policy and delivery tracking.
- Seller KYC/business verification still needs a documented manual review process, data minimization, audit controls and applicable jurisdictional review.
- AI outputs remain advisory. The rules-based risk engine is not a trained model and should not be used as the sole basis for credit, fraud or shipment decisions.
