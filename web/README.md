# PNR Convertor — web

React + TypeScript single-page app for the PNR Convertor API. See
[ADR 0003](../docs/adr/0003-web-frontend.md) for the decisions behind it.

## Develop

```bash
make run           # API on http://localhost:8000 (from the repository root)
make web-dev       # app on http://localhost:5173, proxies /v1 to the API
make web-check     # format, lint, typecheck, tests — what CI runs
```

Configuration lives in `.env` (see `.env.example`): `VITE_API_BASE_URL` for a deployed API,
`API_PROXY_TARGET` for the dev proxy.

## Structure

```
src/
  app/        providers, query client, global styles
  pages/      routes composed from features and entities
  features/   user actions (convert-pnr: form, API calls, exports)
  entities/   domain data and its display (itinerary: zod schemas, formatting, cards)
  shared/     UI kit, HTTP client, errors, config, utilities
  test/       test setup, MSW server, helpers
```

A layer imports only from the layers below it, and other slices only through their `index.ts`
(enforced by ESLint).

## Testing

- Vitest + Testing Library, with MSW for the network.
- `schema.contract.test.ts` parses every backend golden response (`tests/fixtures/pnr`) with the
  frontend schemas: if the API changes shape, this fails.
