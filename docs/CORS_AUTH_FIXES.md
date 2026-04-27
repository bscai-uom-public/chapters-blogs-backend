# CORS and Authentication Notes

## Purpose

This file captures condensed historical notes for CORS and auth-related fixes.
For current contracts, use:

- `README.md`
- `docs/AUTH_README.md`
- `docs/API_AND_CONTRACTS.md`

## Current auth baseline

- Protected routes require `Authorization: Bearer <supabase_access_token>`.
- Header-only auth (`X-User-ID`) is not accepted.
- Tokens are validated against Supabase issuer and JWKS.

## Current CORS baseline

- CORS origins are controlled by `BACKEND_CORS_ORIGINS`.
- Restrict origins in production to known frontend domains.
- Keep `allow_headers` compatible with `Authorization` and JSON API usage.

## Operational reminders

- Disable debug endpoints in production unless explicitly needed.
- Validate environment config after deployment:
  - `SUPABASE_URL`
  - `SUPABASE_JWT_AUDIENCE`
  - `BACKEND_CORS_ORIGINS`
- Test one protected endpoint after each deploy to confirm auth path health.
