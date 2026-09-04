# Architecture and analysis model

RepoLens is organized as a one-way analysis pipeline:

```text
repository path
  -> scanner
  -> Python AST parser + framework detectors
  -> normalized graph document
  -> CLI, local API, and browser UI
```

Each layer accepts structured data from the one before it. The scanner owns safe
filesystem traversal; parsers own source interpretation; the graph engine owns
queries and derived views; product surfaces only consume the graph. This separation
keeps analysis deterministic and prevents a UI or command from needing to execute
target code.

## Graph contents

The graph currently represents repositories, modules, symbols, and framework-aware
elements. Edges express containment and import relationships when an import can be
resolved within the scanned repository. The graph engine supports directed
neighborhoods, N-hop subgraphs, shortest dependency paths, cycles, statistics, and
stable serialization.

An edge is evidence, not a claim about runtime control flow. For example, an import
may be dynamically replaced at runtime, and a route detected from a decorator may
be conditionally registered. Consumers should retain that distinction when
presenting or acting on the graph.

## Framework evidence

The initial framework detectors look for static AST patterns associated with:

- FastAPI route decorators, router inclusion, and `Depends` dependencies.
- SQLAlchemy and SQLModel model declarations.

They do not import FastAPI, SQLAlchemy, SQLModel, or the analyzed repository. That
makes the behavior safe and reproducible, but it also means unusual aliases,
runtime-generated objects, plugins, and custom wrappers may not be recognized.

## Extensibility

The graph document and parser contracts are intentionally typed and normalized so
future language parsers and detectors can add evidence without changing the CLI/API
contract. Python is the supported analysis language today; other source languages
are outside the current release scope.
