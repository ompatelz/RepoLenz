# Architecture Exporters Progress

## Goal

Enable developers, architects, and automated CI pipelines to export RepoLens architecture graphs into industry-standard diagramming formats (Mermaid, PlantUML, Graphviz DOT) and standalone, offline interactive HTML reports without requiring a running server.

## Implemented

- **Exporter Subsystem (`backend/repolens/exporters/`):**
  - `BaseExporter` protocol defining `export(graph: GraphEngine) -> str`.
  - `MermaidExporter`: Generates Mermaid flowchart syntax (`flowchart TD`) with stylized node classes for routes, models, components, and packages.
  - `PlantUmlExporter`: Generates PlantUML component diagram syntax (`skinparam componentStyle uml2`).
  - `DotExporter`: Generates Graphviz DOT syntax (`digraph Architecture`).
  - `HtmlReportExporter`: Generates standalone self-contained HTML snapshot with responsive summary cards, node tables, relationships, cycle banners, and embedded graph JSON data.
  - `get_exporter`: Factory resolving format name aliases (`mermaid`, `plantuml`, `dot`, `html`).
- **CLI Command (`backend/repolens/cli/app.py`):**
  - `repolens export <path> --format mermaid|plantuml|dot|html [--output <file>]`.
- **API Endpoint (`backend/repolens/api/app.py`):**
  - `GET /api/export?format=...` returning raw diagram or HTML report with correct media types (`text/plain` or `text/html`).

## Tests & Verification

- `tests/unit/exporters/test_exporters.py`: Unit tests verifying syntax generation and factory lookup.
- `tests/unit/cli/test_export_command.py`: CLI testing stdout and file output for Mermaid, PlantUML, and HTML.
