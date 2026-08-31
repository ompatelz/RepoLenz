# Python static-analysis milestone

## Delivered

- A safe Python `ast` parser that never imports or executes target code.
- Normalized module, import, symbol, and relationship contracts for future parsers.
- `repolens analyze <path>` with concise terminal and JSON output.
- Decorators, docstrings, signatures, async functions, inheritance, source ranges,
  aliases, relative imports, and isolated syntax-error reporting.

## Known limitations

- Import classification is conservative; repository-wide internal resolution is a
  future graph-layer concern.
