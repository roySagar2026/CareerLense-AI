# Security and privacy

Resumes are personal documents. This is what the application does, and where the limits are.

| Area | Implementation |
|---|---|
| Passwords | Argon2id (`argon2-cffi`), automatic rehash when parameters change. 10–128 characters, at least one letter and one digit. Never logged. |
| Sessions | 15-minute HS256 JWT access token kept **in memory only** in the browser. 7-day opaque refresh token in an `httpOnly`, `SameSite=Lax`, `Secure` (production) cookie scoped to `/api/v1/auth`. Stored as a SHA-256 hash. |
| Token rotation | Each refresh issues a new token and revokes the old one. Replaying a rotated token revokes the whole token family (theft detection). Logout and password change revoke sessions. |
| CSRF | The cookie is only sent to `/auth/*`; `/auth/refresh` and `/auth/logout` additionally require the custom header `X-Requested-With: CareerLens`. All other endpoints use the bearer header, which browsers don't attach cross-site. |
| Account enumeration | Login returns one generic error; forgot-password always answers 202. |
| Rate limiting | DB-backed: 8 failed logins / 15 min per IP and per email, 10 registrations / h and 5 password resets / h per IP. Stored values are keyed hashes. |
| Authorization | Every repository query is filtered by `user_id`. Another user's id returns `404`. Covered by tests (`test_user_isolation`). |
| Uploads | Extension allowlist (`.pdf`, `.docx`), magic-byte check (`%PDF-`, ZIP + `word/document.xml`), 4 MB limit, empty files rejected, filename sanitised (no paths) and never used on disk, zip-bomb guard (uncompressed size cap), original stored as a DB blob and only served through an authenticated endpoint — no public URLs. |
| URL import (SSRF) | `http/https` only, no credentials in URL, ports 80/443 only, hostname resolved and **every** address must be globally routable (blocks loopback, private, link-local incl. cloud metadata `169.254.169.254`, CGNAT, multicast, IPv6 ULA), redirects followed manually (max 3) with re-validation of each hop, 10 s timeout, 1.5 MB cap, content-type allowlist. Failure always points the user to paste text. |
| Injection / XSS | SQLAlchemy parameterised queries only. React escapes output; no `dangerouslySetInnerHTML`. Imported HTML is reduced to text on the server. |
| Headers | CSP (`default-src 'self'`, no inline scripts), HSTS, `X-Content-Type-Options`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy` — set in `vercel.json`, `netlify.toml` and nginx. |
| Secrets | Environment variables only. `.env` is git-ignored; production refuses to start with a missing or weak `JWT_SECRET`. |
| Logging | No passwords, tokens or resume text are logged. Audit rows contain keyed hashes of IP/email. |
| Data control | Users can delete a resume, an analysis, all data, or the account (cascade). The "store original file" setting is honoured. `retention_days` is stored as a preference; automatic purging is **not** implemented yet. |

## Known limitations

- DNS rebinding between validation and connection is a residual SSRF risk (mitigated by validating every redirect hop, not eliminated). Run the backend without access to internal networks if this matters to you.
- Rate limits are per serverless request path using the database, so they are approximate under heavy concurrency.
- The access token cannot be revoked before it expires (15 minutes).
- Resume text and original files are stored unencrypted at the application level; rely on your database provider's encryption at rest.
- Email delivery requires a Resend key; without it, password reset links are not delivered.
- A third-party security review has not been performed.
