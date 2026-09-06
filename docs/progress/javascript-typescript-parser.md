# Feature Progress: JavaScript and TypeScript Static Analysis Parser

## Goal
Extend RepoLens beyond Python to support JavaScript and TypeScript codebases statically and safely. Extract imports, exports, classes, methods, functions, and React components while preserving static-analysis-only guarantees and avoiding fabricated cross-language relationships.

## Implemented
- **Normalized Parser Protocol (`BaseParser`)**: Introduced `BaseParser` in `repolens.parsers.base` defining the standard contract `parse_file(path, module_path=None) -> ModuleAnalysis`.
- **JavaScript & TypeScript Parser (`JavaScriptTypeScriptParser`)**:
  - Pure static lexical scanning with comment and string masking to eliminate false positive tokens.
  - ES6 imports (`import ... from '...'`) and CommonJS requires (`const ... = require('...')`).
  - Standard library (`node:` builtins), third-party, and internal import classification.
  - Class definitions, constructor/method signatures, docstring (JSDoc) capture, and inheritance extraction.
  - Function declarations and arrow/expression functions.
  - React Component detection for both functional components (JSX return, hooks, `React.FC` annotations) and class components (`React.Component` inheritance).
- **Scanner Updates (`RepositoryScanner`)**:
  - Recognition of `.js`, `.jsx`, `.ts`, `.tsx`, `.mjs`, `.cjs` files.
  - Discovery of JS/TS test files (`.test.*`, `.spec.*`, `__tests__/`).
  - Populated `javascript_files` in `RepositoryScan` model.
- **Analysis Pipeline Integration (`analyze_repository`)**:
  - Unified processing of Python and JS/TS modules into a single architecture graph.
  - Deduplicated intra-language module import edges without fabricating cross-language linkages.
  - Added `NodeType.COMPONENT` to both backend models and frontend graph layout / styling.

## Architecture Decisions
- **Zero Execution Guarantee**: Does not spawn Node.js or execute arbitrary JavaScript during analysis; all parsing is deterministic and pure Python static analysis.
- **Masked Token Scanning**: Replaces strings and comments with blank characters preserving exact line breaks and positions, allowing 100% reliable keyword and brace matching.
- **Separate Language Graph Resolution**: Python imports resolve against Python packages; JavaScript imports resolve against relative paths and JS modules, guaranteeing truthful boundaries.

## Tests
- `tests/unit/parsers/test_javascript_parser.py`: 7 unit tests covering ES6/CJS imports, class/method extraction, inheritance, React components, JSDoc, and malformed syntax recovery.
- `tests/unit/scanner/test_polyglot_scanner.py`: Tests polyglot repository discovery.
- `tests/unit/test_polyglot_analysis.py`: End-to-end integration test on mixed Python and TSX project verifying components, routes, and truthful import boundaries.
- Total test suite expanded to 63 passed tests.

## CI Changes
- No new external binary dependencies added. Compatible with existing GitHub Actions workflow.

## Known Limitations
- Complex dynamic runtime imports with computed string templates (`import('./views/' + name)`) cannot be statically resolved without runtime evaluation.
- Monorepos with complex path alias mappings (`tsconfig.json` paths) default to direct relative path resolution.

## Next Work
- Optional AI explanation provider abstraction for explaining architecture nodes and neighborhoods using selected-node context only.
