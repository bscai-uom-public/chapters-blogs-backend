# Documentation Index

This directory contains service documentation for the Chapters Blogs Backend.

## Start here

- [`../README.md`](../README.md): quick setup, environment, endpoint map, security notes.

## Technical docs

- [`ARCHITECTURE.md`](ARCHITECTURE.md): service layout, flow, trust boundaries.
- [`API_AND_CONTRACTS.md`](API_AND_CONTRACTS.md): endpoint catalog, auth and error contracts.
- [`DATA_MODELS_AND_STORAGE.md`](DATA_MODELS_AND_STORAGE.md): collection schema and integrity notes.
- [`AUTH_README.md`](AUTH_README.md): Supabase JWT auth behavior and error handling.
- [`RUN_AND_DEPLOY.md`](RUN_AND_DEPLOY.md): local run and Vercel deployment process.

## Operations and quality docs

- [`TESTING.md`](TESTING.md): local and integration testing guide.
- [`OPERATIONS.md`](OPERATIONS.md): incident response and operational runbook.
- [`CURRENT_ISSUES.md`](CURRENT_ISSUES.md): prioritized known issues and remediation guidance.

## Historical/context docs

- [`CORS_AUTH_FIXES.md`](CORS_AUTH_FIXES.md): historical implementation summary for CORS/auth fixes.
- `AI_AGENT_NOTES.md`: internal notes for agent-assisted work.

## Suggested maintenance routine

When behavior changes:

1. Update the affected technical doc first.
2. Update `../README.md` only for top-level user-facing impacts.
3. Add or update `CURRENT_ISSUES.md` if risk posture changes.
