# pnr-convertor

API that converts raw GDS PNR text (Amadeus, Sabre, Galileo, Worldspan, Apollo, and more to come) into structured, readable itineraries.

## Quick start

Requirements: [uv](https://docs.astral.sh/uv/) and Node 22 (for Prettier).

```bash
make install   # Python + Node tooling
make run       # http://localhost:8000/docs
make check     # lint, typecheck, tests — what CI runs
```

Web app: `make web-install`, then `make web-dev` next to `make run` and open
http://localhost:5173. See [web/README.md](web/README.md).

## Example

```bash
curl -s localhost:8000/v1/convert -H 'content-type: application/json' -d '{
  "pnr": "RP/BUHRO08AA/BUHRO08AA  AA/SU  10JAN26/0915Z   ZX7K2P\n  1.POPESCU/ANDREI MR\n  2  RO 391 Y 15MAR 7 OTPCDG HK1  0710 0920"
}'
```

Add `?format=text` or `?format=html` for a readable itinerary instead of JSON:

```text
FLIGHT ITINERARY
Booking reference: ZX7K2P

PASSENGERS
  1. POPESCU/ANDREI MR - Adult

TRIP 1: Bucharest (OTP) to Paris (CDG)
Sun 15 Mar 2026 | Direct | 3h 10m | 1,856 km (1,153 mi)

  RO 391  Tarom | Class Y | Confirmed
  Depart  Sun 15 Mar 2026 07:10  Bucharest (OTP), Henri Coanda International Airport
  Arrive  Sun 15 Mar 2026 09:20  Paris (CDG), Charles de Gaulle International Airport
  Flight  3h 10m | 1,856 km (1,153 mi)

Times are local at each airport.
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Web app](web/README.md)
- [Roadmap](docs/ROADMAP.md)
- [Data sources & licenses](docs/DATA_SOURCES.md)
- [Agent / contributor guidelines](AGENTS.md)

## License

Proprietary. © 2026 KitTsuky. All rights reserved. No use, copying or distribution without written
permission; see [LICENSE](LICENSE). Third-party data keeps its own licenses
([data sources](docs/DATA_SOURCES.md)).
