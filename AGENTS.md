# Agent & contributor guidelines

Rules for anyone (human or AI agent) changing this repository. Read
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/ROADMAP.md](docs/ROADMAP.md) first.

## What this project is

An HTTP API that converts raw GDS PNR text (Amadeus, Sabre, Galileo, Worldspan and Apollo) into a
structured, enriched itinerary. Stack: Python 3.12, FastAPI, Pydantic v2, uv, pytest, Ruff, mypy.

## Commands

| Task                 | Command        |
| -------------------- | -------------- |
| Install              | `make install` |
| Run locally          | `make run`     |
| Everything CI checks | `make check`   |
| Auto-format          | `make format`  |
| Regenerate goldens   | `make golden`  |

`make check` must pass before any change is considered done.

## Architecture rules (non-negotiable)

Dependencies point inward only:

```
api  ──►  application  ──►  domain
              │                ▲
              ▼                │
           parsing  ───────────┘
infrastructure ──► application ports
bootstrap.py wires everything (composition root)
```

- `domain/` imports nothing from the project and nothing from FastAPI/Pydantic.
- `parsing/` depends only on `domain/`. One sub-package per GDS.
- `application/` orchestrates use cases and defines ports (`Protocol`s) for external needs.
- `infrastructure/` implements ports (clock, reference data, caches, ...).
- `api/` is a thin adapter: validate → call use case → map to response schema. No logic.
- Only `bootstrap.py` instantiates concrete classes. Everything else receives dependencies.
- API schemas (`api/v1/schemas.py`) are separate from domain models and mapped explicitly.
  Changing them is a breaking change; add a new field instead of renaming, or create `/v2`.

## Code standards

- Fully typed; `mypy --strict` must pass. No `Any` unless at a true boundary.
- Domain models: `@dataclass(frozen=True, slots=True)`. Collections in models are tuples.
- Parsers are pure and stateless: same text + context → same result. No I/O, no clock.
- Expected failures raise a subclass of `PnrConvertorError` with a stable `code`.
  Recoverable per-line issues become `ParseWarning`s instead of exceptions.
- Prefer clear names over comments. Comment only the non-obvious "why". No banner comments,
  no commented-out code.
- Formatting: Ruff for Python, Prettier for Markdown/JSON/YAML. Never hand-format.
- Keep functions small; extract a helper rather than nesting beyond two levels.

## Privacy (PNRs contain personal data)

- Never log PNR text, names, contacts or document numbers. Log counts and formats only.
- Error responses and `ParseWarning` messages must not echo input text.
- Test fixtures use fictional names only (e.g. `DOE/JANE`, `POPESCU/ANDREI`). Never commit a
  real PNR, even a partial one.

## Testing

- Every behavior change comes with tests. Coverage must stay ≥ 90%.
- Layout: `tests/unit` (pure logic), `tests/integration` (HTTP via `TestClient`),
  `tests/golden` (end-to-end fixture → expected JSON).
- Tests are deterministic: use `FixedClock` / `REFERENCE_DATE` from `tests/conftest.py`.
- Golden workflow: add `tests/fixtures/pnr/<gds>/<case>.txt`, run `make golden`, then **review
  the generated `.expected.json` by hand** before committing. Never regenerate goldens just to
  make a failing test pass without understanding the diff.

## How to add a new GDS format

1. Add the value to `GdsFormat` in `domain/models.py`.
2. Create `parsing/<gds>/` with `patterns.py` (regexes) and `parser.py` implementing
   `PnrParser` (`gds`, `detect`, `parse`).
3. `detect` returns 1.0 only for unambiguous markers (e.g. a header), lower for heuristics.
4. Register it in `bootstrap.build_parser_registry`.
5. Add unit tests plus at least two golden fixtures (simple + edge case).

## Git workflow

- Never commit to `main` directly. Branch per logical change: `feat/…`, `fix/…`, `chore/…`,
  `docs/…`, `refactor/…`, `test/…`.
- Conventional Commits: `feat(parsing): parse Sabre air segments`.
- One logical change per commit; one roadmap item (or smaller) per PR.
- Ask the maintainer to review before committing and before pushing.
