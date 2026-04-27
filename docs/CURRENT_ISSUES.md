# Current Issues Register

## Snapshot

- Service: Chapters Blogs Backend
- Scope: codebase-level behavior and operational risk review
- Last reviewed: 2026-04-23
- Method: static review of endpoint, service, security, status, and schema layers

## Severity: Critical

### 1) Legacy identity spoofing risk (resolved)

Evidence:

- Historical behavior used to accept `X-User-ID` directly.

Impact:

- If header passthrough were enabled, untrusted callers could spoof user identity.

Recommended fix:

- Keep Bearer-only auth in `app/core/security.py`.
- Do not reintroduce trusted header fallback.

Verification approach:

- Send a direct request with forged `X-User-ID` and no bearer token; confirm `401`.

### 2) Token audience validation (resolved)

Evidence:

- `app/core/security.py` validates audience when `SUPABASE_JWT_AUDIENCE` is configured.

Impact:

- Invalid audience tokens should now be rejected.

Recommended fix:

- Keep `SUPABASE_JWT_AUDIENCE` aligned with Supabase token settings.
- Maintain tests for valid and invalid `aud` claims.

Verification approach:

- Attempt auth with token from different audience and confirm `401`.

### 3) Debug endpoints potentially exposed by permissive default gating

Evidence:

- `app/services/status.py` defaults `DEBUG_ENDPOINTS_ENABLED` to `true`.
- Debug routes in `app/api/v1/endpoints/blogs.py` can expose sensitive runtime/auth information.

Impact:

- Production information leakage risk (headers, auth context, user listings, token helper behavior).

Recommended fix:

- Default to debug routes disabled unless explicitly enabled in development.
- Restrict debug routes at gateway and/or remove them from production build.

Verification approach:

- In production-like config, call debug routes and confirm they are inaccessible.

## Severity: High

### 4) Health endpoint status-code propagation bug

Evidence:

- In `app/api/v1/endpoints/blogs.py`, non-200 status is assigned to a local `Response()` object that is not returned.

Impact:

- Degraded/unhealthy conditions may still emit HTTP 200, reducing monitoring reliability.

Recommended fix:

- Inject `response: Response` parameter and set `response.status_code` directly.

Verification approach:

- Simulate dependency outage and confirm `/health` returns non-200 status code.

### 5) Orphan reply risk in blog deletion flow

Evidence:

- `app/services/blog.py` deletes comments first, then queries comments to collect IDs for reply deletion.

Impact:

- Replies linked to deleted comments can remain orphaned in `Replies`.

Recommended fix:

- Fetch comment IDs first, then delete replies, then delete comments (or use transaction/session strategy).

Verification approach:

- Create blog->comment->reply tree, delete blog, verify all related docs are removed.

### 6) Unbounded recursive reply traversal

Evidence:

- `fetch_replies` in `app/services/blog.py` recursively fetches children with no explicit max depth/cycle guard.

Impact:

- Deep nesting can cause high latency, heavy DB churn, or recursion failure.

Recommended fix:

- Add depth limit and/or iterative traversal strategy.
- Add guardrails for pathological nesting.

Verification approach:

- Seed deep nested replies and measure response behavior against configured bounds.

## Severity: Medium

### 7) Exception usage inconsistencies

Evidence:

- Mixed use of exception classes and instances (for example `raise InternalServerException` vs instantiated forms).
- Ownership mismatch exception type used in one comment update path.

Impact:

- Inconsistent error semantics and maintainability friction.

Recommended fix:

- Standardize exception raising pattern and audit ownership exception mapping.

Verification approach:

- Add focused tests asserting correct status/message per failure path.

### 8) Fragile DB dependency lifecycle helper

Evidence:

- `get_database` in `app/db/database.py` closes global client in `finally`.

Impact:

- Future DI usage can accidentally close shared client per request.

Recommended fix:

- Remove client close from request-scoped dependency; close once on app shutdown.

Verification approach:

- Add repeated-request test using dependency and assert stable DB connectivity.

### 9) Mutable default list fields in schemas

Evidence:

- `replies: List[...] = []` in multiple models.

Impact:

- Potential shared-state pitfalls and model maintenance issues.

Recommended fix:

- Use `Field(default_factory=list)` consistently.

Verification approach:

- Unit tests that mutate one instance and ensure others remain unaffected.

## Severity: Low

### 10) Dependency/config drift

Evidence:

- Unused SQL-oriented config/dependencies are present while service is Mongo-focused.

Impact:

- Larger maintenance and security surface than necessary.

Recommended fix:

- Remove unused config and packages after validation.

Verification approach:

- Run dependency audit and startup/import checks after cleanup.

### 11) Limited automated tests

Evidence:

- Existing `tests/test_auth.py` is script-style rather than full automated suite coverage.

Impact:

- Regressions in auth, cascade deletion, and health behavior may ship unnoticed.

Recommended fix:

- Add prioritized automated tests for critical/high issue paths first.

Verification approach:

- CI gating on new tests plus smoke checks.

## Suggested remediation order

1. Fix critical auth/debug exposure and audience validation.
2. Fix health status code and blog deletion integrity.
3. Add recursion safeguards and test coverage for auth/deletion/health.
4. Clean up medium/low maintainability and dependency issues.
