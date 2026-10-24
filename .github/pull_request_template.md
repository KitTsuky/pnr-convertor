## What

<!-- One or two sentences: what changes and why. Link the roadmap item or issue: Closes #123 -->

## How

<!-- Key implementation decisions a reviewer should know about. -->

## Testing

<!-- New/updated tests, golden fixtures added, manual checks. -->

## Checklist

- [ ] `make check` passes locally
- [ ] Tests cover the change (golden `.expected.json` reviewed by hand, if touched)
- [ ] No breaking change to `api/v1/schemas.py` (or it is intentional and documented)
- [ ] No real PNR data, names or contacts in code, fixtures or logs
- [ ] Docs updated (`ARCHITECTURE.md`, `ROADMAP.md`, `AGENTS.md`) if behavior or structure changed
