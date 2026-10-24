# Architecture

## Goals

1. **Correctness on messy input.** PNR text comes from many GDS terminals, copied through
   email clients and chat tools. Parsing must be tolerant and must report what it skipped.
2. **Extensibility.** New GDS formats, data sources and output formats are added by writing a new
   module and registering it, not by editing existing code (open/closed principle).
3. **Privacy by default.** PNRs contain personal data; nothing is stored or logged.
4. **A stable public contract.** Internal refactors never change the API.

## Style: ports & adapters (hexagonal)

```
                ┌──────────────────────────────────────────────┐
  HTTP ───────► │ api/            FastAPI routes, schemas,     │
                │                 problem+json errors          │
                └───────────────┬──────────────────────────────┘
                                ▼
                ┌──────────────────────────────────────────────┐
                │ application/    use cases (ConvertPnr)       │
                │                 ports: Clock, AirportRepo... │
                └───────┬───────────────────────────▲──────────┘
                        ▼                           │ implements
                ┌───────────────┐         ┌─────────┴──────────┐
                │ parsing/      │         │ infrastructure/    │
                │  registry     │         │  SystemClock,      │
                │  amadeus/     │         │  reference data,   │
                │  sabre/ ...   │         │  caches ...        │
                └───────┬───────┘         └────────────────────┘
                        ▼
                ┌──────────────────────────────────────────────┐
                │ domain/         ParsedPnr, FlightSegment,    │
                │                 Passenger, errors            │
                └──────────────────────────────────────────────┘
```

`bootstrap.py` is the composition root: it builds the object graph once at startup and stores it
on `app.state.container`. Tests build their own container (e.g. with `FixedClock`).

## Request flow: `POST /v1/convert`

1. `ConvertRequest` validates size and shape; unknown fields are rejected.
2. `ConvertPnr.execute` normalizes the text (line endings, tabs, case).
3. `ParserRegistry.resolve` picks the parser: explicit `gds`, or the highest `detect()` score
   above `MIN_DETECTION_CONFIDENCE`.
4. The parser walks the text line by line, producing domain objects and `ParseWarning`s.
5. `ItineraryEnricher` resolves airports and airlines through ports, converts local times to
   timezone-aware datetimes, and groups segments into journeys (a break over 24h is a stopover).
6. `ConvertResponse.from_domain` maps the domain model to the public schema.

## Key decisions

| Decision                                     | Reason                                                                                                    |
| -------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Python + FastAPI                             | Fast iteration on regex-heavy parsing; mature data ecosystem. See [ADR 0001](adr/0001-python-fastapi.md). |
| Domain models are dataclasses, not Pydantic  | Domain stays framework-free; validation belongs at the boundary.                                          |
| Separate API schemas                         | Public contract can evolve independently (`/v1`, `/v2`).                                                  |
| Year inference via `reference_date`          | GDS dates have no year; clients can pass the display date for historical PNRs.                            |
| Datetimes are airport-local until enrichment | The GDS shows local times; converting needs timezone data, which is an enrichment concern.                |
| Warnings instead of failing                  | One unparseable line should not discard an otherwise valid itinerary.                                     |
| RFC 9457 problem details                     | Standard, machine-readable errors with stable `code` values.                                              |

## Extension points

| To add…                         | Implement                       | Register in                       |
| ------------------------------- | ------------------------------- | --------------------------------- |
| A GDS format                    | `PnrParser` in `parsing/<gds>/` | `bootstrap.build_parser_registry` |
| A reference data source         | a port in `application/ports`   | adapter in `infrastructure/`      |
| An output format (HTML, PDF...) | a renderer (Phase 4)            | renderer registry                 |
| An API version                  | `api/v2/` package               | `main.create_app`                 |
