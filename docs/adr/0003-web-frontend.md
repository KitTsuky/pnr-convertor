# ADR 0003: Web frontend

- Status: accepted
- Date: 2026-10-24

## Context

Agents need a page to paste a PNR and read the itinerary, without calling the API by hand. The
API is the product; the page is one client of it and must never fork its rules.

## Decision

A React + TypeScript single-page app in `web/`, in the same repository as the API, built with Vite.

- Layers follow Feature-Sliced Design: `app` → `pages` → `features` → `entities` → `shared`. A
  layer imports only from lower layers, and another slice only through its `index.ts`; ESLint
  enforces both.
- HTTP goes through one `axios` instance; every failure becomes an `ApiError` that reads RFC 9457
  problem details.
- Responses are validated at runtime with `zod`. A contract test parses every backend golden
  response with the frontend schemas and fails if a field is missing or mistyped.
- Forms use `react-hook-form` with the same `zod` schemas; server state uses TanStack Query.
- UI: Tailwind CSS with a small in-repo kit built on Radix primitives (shadcn/ui style), neutral
  palette, Inter, light and dark themes. Fonts are self-hosted: no third-party requests.
- The dev server proxies `/v1` to the API, so the browser stays same-origin and the API needs no
  CORS.

## Consequences

- One pull request can change the API and the page together; CI checks both.
- The frontend never trusts the network: a contract drift fails a test before it reaches users.
- More tooling (Node, npm lockfile) in a Python repository; kept isolated in `web/`.
