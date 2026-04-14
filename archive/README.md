# Archive Index

This directory contains non-core materials moved out of the active project root.

## Purpose

- Keep the root focused on core application code and required setup docs.
- Preserve historical notes and one-off scripts for traceability.

## Structure

- `archive/docs/` historical or duplicate documentation
- `archive/scripts/` one-off operational/debug helper scripts

## Restore Guidance

If an archived item becomes active again, move it back with Git so history is preserved.

Example:

```bash
git mv archive/docs/DOCKER.md DOCKER.md
```

or

```bash
git mv archive/scripts/backend/check_status.py backend/check_status.py
```

## Safety Notes

- Archived files are still versioned.
- No active runtime depends on archived scripts by default.
- Keep new one-off notes/scripts here unless they are promoted to supported workflow.
