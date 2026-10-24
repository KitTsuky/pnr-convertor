# pnr-convertor

API that converts raw GDS PNR text (Amadeus, and more to come) into structured, readable itineraries.

## Quick start

Requirements: [uv](https://docs.astral.sh/uv/) and Node 22 (for Prettier).

```bash
make install   # Python + Node tooling
make run       # http://localhost:8000/docs
make check     # lint, typecheck, tests — what CI runs
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Agent / contributor guidelines](AGENTS.md)
