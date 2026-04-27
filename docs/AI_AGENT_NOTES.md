# Chapters Blogs Backend AI Agent Notes

## High-Risk Zones
- `app/core/security.py`: auth identity extraction and JWT validation controls.
- `app/api/v1/endpoints/blogs.py`: debug/public/protected route boundaries.
- `app/services/blog.py`: ownership enforcement, recursive replies, like counters, delete cascades.

## Known Pitfalls
- Supabase URL or audience misconfiguration can break token validation.
- Debug routes are co-located with production routes and controlled by environment logic.
- Delete ordering for blog comments/replies likely has orphan risk.

## Safe Edit Strategy
1. Read endpoint contract and schema before touching service methods.
2. Keep ownership checks intact for all mutating operations.
3. Preserve response schema fields expected by frontend.
4. If touching auth, verify bearer-only flow on protected routes.

## Validation Checklist
- Protected routes still reject unauthorized and non-owner updates/deletes.
- Public routes remain unauthenticated.
- Comment/reply tree responses still serialize as expected.
- Like/unlike updates remain idempotent and count-safe.

## Recommended Follow-Up Work
- Add automated auth and service behavior tests.
- Add explicit production guard for debug routes.
- Add tests around delete cascades and nested replies.
