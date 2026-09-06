# Semantic Zoom and Graph Navigation

## Overview

As repositories grow in size, rendering all classes, functions, methods, routes, models,
and modules at once creates cognitive overload. Feature 3 introduces **Semantic Zoom and
Graph Navigation** to RepoLens, empowering engineers to interactively explore architectures
at multiple levels of abstraction.

## Key Capabilities

1. **Multi-level Hierarchy (Semantic Zoom)**
   - Supported levels:
     - `All`: Full architecture map.
     - `Repo`: Repository boundary and overarching packages.
     - `Modules`: File- and package-level module hierarchy.
     - `Symbols`: Class-, function-, route-, and model-level entities.
   - Connected directly to the `/api/graph?level={level}` backend endpoint to retrieve
     statistically consistent filtered subgraphs and dynamic cycle analyses.

2. **Breadcrumb Navigation & Drill-down**
   - Clickable breadcrumbs path (`Scope: All / Package / Module`) reflects current focus.
   - Users can double-click package or module nodes on the canvas or click "Drill into"
     in the Inspector panel to narrow the viewport to that component and its children.
   - Child modules, classes, methods, functions, routes, and models are scoped cleanly,
     and users can return up the hierarchy with one click.

3. **Neighborhood Focus Mode (1-hop, 2-hop, 3-hop)**
   - When inspecting any node, users can toggle Focus Mode to isolate its direct dependencies
     (1-hop) or extended influence radius (2-hop or 3-hop).
   - Unrelated nodes are hidden while maintaining structural relationships and edges.
   - Active focus is highlighted with a clear visual badge and quick-reset action.

4. **Package Collapse and Expansion**
   - Allows collapsing whole packages into single summary nodes, eliminating noise from
     internal helper functions and classes while preserving cross-package boundaries.

5. **Resilient Empty and Loading States**
   - Contextual empty states provide actionable recovery links (e.g. "Clear search",
     "Reset scope", "Reset focus", "Show all types").
