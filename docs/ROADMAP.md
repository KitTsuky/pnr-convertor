# Roadmap

Each phase ends in a releasable state: `make check` passes and the API is usable. Each bullet is
roughly one PR.

## Phase 0 — Foundation ✅

- [x] Project layout (ports & adapters), uv, Ruff, mypy strict, pytest, Prettier
- [x] App factory, settings via env (`PNR_*`), composition root
- [x] `GET /health`, RFC 9457 error responses, PII-safe validation errors
- [x] CI workflow, Dockerfile, agent guidelines

## Phase 1 — Amadeus core parsing ✅

- [x] Domain model: `ParsedPnr`, `FlightSegment`, `Passenger`, `SegmentStatus`
- [x] Parser registry with auto-detection
- [x] Amadeus: record locator, passenger names, air segments, `+1` arrivals, year inference
- [x] `POST /v1/convert`
- [x] Unit, integration and golden tests

## Phase 2 — Enrichment ✅

- [x] Ports: `AirportRepository`, `AirlineRepository`
- [x] Adapters backed by bundled datasets (OurAirports / `airportsdata`, OpenFlights airlines)
- [x] Timezone-aware departure/arrival (UTC + local with offset)
- [x] Flight duration, layover times, overnight/connection detection
- [x] Group segments into journeys (outbound / return) by layover threshold
- [x] Extend response schema (additive fields only)
- [x] Distances on the WGS84 ellipsoid (matches IATA ticketed point mileage), status descriptions

## Phase 3 — More GDS formats

- [x] Sabre itinerary display (`*I` / `*IA`), letter weekdays, 12-hour times
- [x] Sabre `*A`: passengers (multi-name items), record locator (signature line), phones, married segments
- [x] Sabre electronic tickets (`TE` items in `TKT/TIME LIMIT`), matched to passengers by abbreviated name, with issue date
- [ ] Sabre emails, infants (needs anonymized samples)
- [ ] Sabre `VI*`: terminals, equipment, elapsed time, miles
- [x] Travelport Galileo booking file (`*R` / `*I`): header locator, names with type suffixes and infants, segments with `#` / `*` / `-` arrival markers
- [x] Galileo phone field (`FONE-` with numbered continuation lines)
- [x] Galileo and Apollo electronic tickets from a pasted `*HTE` display: number, holder by name, issue date, plating carrier
- [x] Travelport Worldspan (`*R`): `1P-` locator, names with titles and type codes, segments with `#1` day offset, phones (`P-`), tickets (`T-`)
- [x] Travelport Apollo (`*R`): header shared with Galileo, segments without a dot, 12-hour times with `+` day offset, names with spaced titles, child (`*C08`) and infant (`I/`) items, phones (`FONE-`)
- [ ] Detection conflicts: score-based tie handling + tests with ambiguous inputs
- [ ] Golden fixtures for each format (≥ 5 cases each)

## Phase 4 — Output renderers

- [ ] Renderer port + registry; `format` query parameter (`json` default)
- [ ] Plain text and HTML itinerary (Jinja2 templates)
- [ ] PDF (WeasyPrint)
- [ ] Localization (EN, RO) for rendered outputs

## Phase 5 — Production hardening

- [ ] Structured JSON logging with request IDs
- [ ] API keys (hashed), per-key rate limiting
- [ ] Request size limits at the server level, timeouts
- [ ] Metrics + tracing (OpenTelemetry), `/ready` probe
- [ ] Versioned OpenAPI contract test (fails on breaking changes)
- [ ] Deployment (container registry + hosting), environment configs

## Phase 6 — Richer PNR content

- [x] Amadeus tickets (`FA`), seats (`SSR NSST` / `RQST` / `SEAT`), contacts (`AP` / `APE`)
- [x] Ticket numbers for Sabre (`TE`) and Travelport (`*HTE`)
- [x] Codeshare operator (`OPERATED BY` lines) as `operated_by` on every format
- [ ] `FHE`, fare elements, ticket time limits
- [ ] SSR/OSI (meals, seats, special assistance), APIS documents (masked)
- [x] Amadeus passenger types (`CHD`, `INS`, ...), dates of birth, lap infants (`INF`), infant tickets
- [ ] Remarks
- [ ] Non-air segments: hotel, car, rail, `ARNK`

## Phase 7 — Optional

- [ ] Web UI (paste → itinerary)
- [ ] Batch endpoint
- [ ] LLM fallback for unparseable lines, behind a feature flag, with PII redaction
