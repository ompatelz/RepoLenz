# AI Architecture Explainer Progress

## Goal

Provide bounded, optional architectural intelligence and node explanations directly derived from static analysis, dependency structure, framework routing, and data models—without sending entire codebases over the network or requiring mandatory cloud API keys for core developer flows.

## Implemented

- **Provider Abstraction (`backend/repolens/ai/`):**
  - `BaseExplanationProvider` protocol with unified `explain(context: NodeExplanationContext) -> NodeExplanation` signature.
  - `OfflineExplanationProvider`: High-fidelity, deterministic rule-based architectural synthesizer evaluating fan-in, fan-out, structural roles, framework contracts, coupling, and concrete architectural recommendations completely offline.
  - `OpenAICompatibleProvider`: Zero-dependency, standard library HTTP client communicating with OpenAI or local OpenAI-compatible backends (Ollama, vLLM, LM Studio, etc.) via `REPOLENS_AI_API_KEY` / `OPENAI_API_KEY` and configurable base URLs.
  - `MockExplanationProvider`: Deterministic mock implementation for automated test suites.
  - `get_provider(name)` factory mapping environment variables and CLI parameters.

- **Bounded Context Extractor (`backend/repolens/ai/context.py`):**
  - Strictly limits context to the requested node, 1-hop direct neighbors, incoming/outgoing edges, and related framework routes and data models.
  - Traversal-safe source snippet extractor that verifies path containment within the repository root, ignores binaries and files > 2MB, and caps line ranges (default maximum 60 lines).
  - Explicit guarantee: never uploads or transmits entire repositories.

- **HTTP API Extension (`backend/repolens/api/app.py`):**
  - Added `POST /api/nodes/{node_id}/explain` and `GET /api/nodes/{node_id}/explain` endpoints supporting optional `?provider=` query parameter.
  - Returns structured `NodeExplanation` JSON schema.

- **Command-Line Interface (`backend/repolens/cli/app.py`):**
  - Added `repolens explain <path> --node <node_id> [--provider ...]` supporting human-readable formatted output and machine-readable `--json`.
  - Updated `repolens serve` to pass the analyzed repository root into the local HTTP API app.

- **Web Explorer Integration (`frontend/src/`):**
  - Added `NodeExplanation` TypeScript contract in `frontend/src/types.ts`.
  - Added interactive "Architecture Intelligence" section to the React Flow inspector pane in `frontend/src/App.tsx`.
  - Includes asynchronous loading state, error retry handling, role & provider badges, impact analysis, dependency context, and actionable recommendations.
  - Polished dark developer-tool styles added in `frontend/src/styles.css`.
  - Production frontend bundle rebuilt and synchronized to `backend/repolens/web/`.

## Architecture Decisions

1. **Local-First / Zero Mandatory API Keys:**
   - The default provider is `offline`. Developers using RepoLens immediately receive rich structural analysis without configuring external credentials or network access.
2. **Strict Context Budget:**
   - Rather than serializing whole files or full repository trees, the context builder extracts only 1-hop topological connectivity and a tight source excerpt (capped at 60 lines).
3. **No Heavy Cloud SDKs:**
   - The OpenAI-compatible client uses Python's standard library (`urllib.request`), avoiding heavy external client libraries and keeping RepoLens's runtime dependencies lean.

## Tests & Verification

- `tests/unit/ai/test_context_builder.py`: Validates bounded snippet extraction, max line caps, path traversal safety, and 1-hop neighbor gathering.
- `tests/unit/ai/test_providers.py`: Validates offline rule synthesis, mock provider output, missing API key errors, and provider resolution.
- `tests/unit/api/test_ai_explanation_api.py`: Validates `POST` and `GET` `/api/nodes/{id}/explain` endpoints and 404 behavior.
- `tests/unit/cli/test_explain_command.py`: Validates CLI human-readable formatting, JSON mode, and missing node error handling.
- `frontend/src/`: Vitest test suite passes (15 tests); Vite production build passes.
- Wheel smoke test verified against isolated environment.

## Known Limitations

- The `openai` provider requires external network connectivity and a valid API key or local compatible server endpoint.
