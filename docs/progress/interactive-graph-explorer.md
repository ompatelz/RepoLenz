# Interactive graph explorer

## Goal

Turn the browser shell into a usable visual architecture map while keeping the graph
document and static-analysis pipeline as the single source of truth.

## Implemented

- Locally bundled React Flow canvas with deterministic hierarchy placement.
- Directed, labeled architecture edges, pan/zoom controls, and minimap navigation.
- Search and node-type filters that retain only relationships whose endpoints are shown.
- Node selection connected to the existing source and relationship inspector.
- Rebuilt frontend assets included with the Python package.
- Vitest coverage for stable placement and filter-aware edge selection.

## Architecture decisions

The initial layout uses typed hierarchy columns rather than a force simulation. This
keeps refreshes stable and avoids adding a layout engine solely for small and medium
graphs. The frontend does not infer dependencies; it renders only graph-document edges.

## Tests and CI

`npm run test` runs graph-layout behavior tests. GitHub Actions now executes that test
command after `npm ci` and before the production build.

## Known limitations

Very large repositories still receive the complete graph document. Semantic zoom and
server-side subgraph requests are the next performance-focused product slice.
