# ADR 0002: Ports & adapters architecture

- Status: accepted
- Date: 2026-10-24

## Context

The product will grow along independent axes: more GDS formats, more reference data sources,
more output formats, and new API versions. Each should be addable without touching the others.

## Decision

Layered ports & adapters: `domain` (pure models) ← `parsing` and `application` (use cases and
ports) ← `api` and `infrastructure` (adapters). A single composition root (`bootstrap.py`) wires
concrete implementations. Each GDS parser implements a `PnrParser` protocol and is selected by a
registry.

## Consequences

- New capabilities are new modules plus one registration line.
- Use cases are testable without HTTP or real data sources.
- Slightly more files and explicit mapping code (domain → API schema) than a flat FastAPI app.
