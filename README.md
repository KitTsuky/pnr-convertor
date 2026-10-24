# pnr-convertor

API that converts raw GDS PNR text (Amadeus, Sabre, Galileo, Worldspan, Apollo, and more to come) into structured, readable itineraries.

## Quick start

Requirements: [uv](https://docs.astral.sh/uv/) and Node 22 (for Prettier).

```bash
make install   # Python + Node tooling
make run       # http://localhost:8000/docs
make check     # lint, typecheck, tests — what CI runs
```

## Example

```bash
curl -s localhost:8000/v1/convert -H 'content-type: application/json' -d '{
  "pnr": "RP/BUHRO08AA/BUHRO08AA  AA/SU  10JAN26/0915Z   ZX7K2P\n  1.POPESCU/ANDREI MR\n  2  RO 391 Y 15MAR 7 OTPCDG HK1  0710 0920"
}'
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Data sources & licenses](docs/DATA_SOURCES.md)
- [Agent / contributor guidelines](AGENTS.md)
