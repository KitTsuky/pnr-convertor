# ADR 0001: Python + FastAPI

- Status: accepted
- Date: 2026-10-24

## Context

The core work is parsing loosely formatted terminal text with many variants per GDS, then
enriching it with reference data (airports, airlines, timezones) and rendering documents.
Throughput needs are modest: parsing one PNR takes about a millisecond.

Options considered: Python/FastAPI, Go, TypeScript/Node.

## Decision

Python 3.12 with FastAPI and Pydantic v2, managed by uv.

## Consequences

- Fast iteration on regex-based parsers; concise, parametrized tests with pytest.
- Mature libraries for timezones, reference data and HTML/PDF rendering.
- Runtime type safety only at boundaries (Pydantic); internal safety relies on `mypy --strict`.
- Raw performance is lower than Go, which is irrelevant at the expected load. Horizontal scaling
  is straightforward because the service is stateless.
