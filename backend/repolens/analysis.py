"""End-to-end static analysis pipeline from a repository to a graph document."""

from __future__ import annotations

import os
from pathlib import Path

from repolens.cache import AnalysisCache
from repolens.detectors import FrameworkDetector
from repolens.detectors.frameworks import DatabaseModel, FrameworkAnalysis
from repolens.models import Edge, EdgeType, GraphDocument, Node, NodeType
from repolens.parsers import JavaScriptTypeScriptParser, PythonAstParser
from repolens.parsers.models import ModuleAnalysis, Symbol, SymbolKind
from repolens.scanner import RepositoryScanner


def analyze_repository(path: Path | str, *, use_cache: bool = True) -> GraphDocument:
    """Build a graph, reusing a fingerprint-validated local cache by default."""
    if use_cache:
        graph, _ = AnalysisCache().get_or_create(
            path, lambda: analyze_repository(path, use_cache=False)
        )
        return graph
    scan = RepositoryScanner().scan(path)
    root = Path(scan.root)
    py_parser = PythonAstParser()
    js_parser = JavaScriptTypeScriptParser()
    detector = FrameworkDetector()
    repo_id = f"repository:{scan.name}"
    nodes: list[Node] = [Node(id=repo_id, type=NodeType.REPOSITORY, name=scan.name, path=".")]
    edges: list[Edge] = []
    modules: dict[str, str] = {}
    js_modules: dict[str, str] = {}
    python_parsed: list[tuple[str, str, ModuleAnalysis, FrameworkAnalysis]] = []
    all_parsed: list[tuple[str, str, ModuleAnalysis]] = []

    for relative in scan.python_files:
        module = relative.removesuffix(".py").replace("/__init__", "").replace("/", ".")
        node_id = f"module:{module}"
        modules[module] = node_id
        nodes.append(
            Node(id=node_id, type=NodeType.MODULE, name=module.split(".")[-1], path=relative)
        )
        edges.append(Edge(source=repo_id, target=node_id, type=EdgeType.CONTAINS))
        parsed = py_parser.parse_file(root / relative, module)
        fw = detector.detect_file(root / relative, module)
        python_parsed.append((node_id, relative, parsed, fw))
        all_parsed.append((node_id, relative, parsed))

    for relative in scan.javascript_files:
        raw_path = Path(relative)
        stem = raw_path.stem
        ext = raw_path.suffix
        clean_rel = relative.removesuffix(ext)
        if stem == "index" and len(raw_path.parts) > 1:
            clean_rel = str(raw_path.parent).replace("\\", "/")
        module = clean_rel.replace("/", ".")
        node_id = f"module:{module}"
        modules[module] = node_id
        js_modules[clean_rel] = node_id
        js_modules[relative] = node_id
        js_modules[f"./{clean_rel}"] = node_id
        nodes.append(Node(id=node_id, type=NodeType.MODULE, name=stem, path=relative))
        edges.append(Edge(source=repo_id, target=node_id, type=EdgeType.CONTAINS))
        parsed = js_parser.parse_file(root / relative, module)
        all_parsed.append((node_id, relative, parsed))

    symbols_by_id: dict[str, Symbol] = {}
    for _, _, parsed in all_parsed:
        for sym in parsed.symbols:
            symbols_by_id[sym.id] = sym

    models_by_module_name: dict[tuple[str, str], DatabaseModel] = {}
    models_by_name: dict[str, list[tuple[str, DatabaseModel]]] = {}
    for _, _, _, fw in python_parsed:
        for model in fw.models:
            models_by_module_name[(model.module, model.name)] = model
            models_by_name.setdefault(model.name, []).append((model.module, model))

    for _, _, parsed, _ in python_parsed:
        for symbol in parsed.symbols:
            if (
                symbol.kind == SymbolKind.CLASS
                and (parsed.module, symbol.name) not in models_by_module_name
            ):
                is_submodel = False
                for base in symbol.bases:
                    base_name = base.split(".")[-1]
                    if base_name in models_by_name:
                        is_submodel = True
                        break
                if is_submodel:
                    derived_model = DatabaseModel(
                        name=symbol.name,
                        module=parsed.module,
                        line=symbol.line_start,
                        table_name=None,
                        fields=[],
                        bases=symbol.bases,
                    )
                    models_by_module_name[(parsed.module, symbol.name)] = derived_model
                    models_by_name.setdefault(symbol.name, []).append(
                        (parsed.module, derived_model)
                    )

    model_node_ids: dict[tuple[str, str], str] = {}
    class_node_ids: dict[tuple[str, str], str] = {}
    route_count = 0
    model_count = 0
    component_count = 0
    symbol_count = 0

    for module_id, relative, parsed in all_parsed:
        for symbol in parsed.symbols:
            matching_model = models_by_module_name.get((parsed.module, symbol.name))
            if matching_model is not None:
                node_id = f"model:{symbol.id}"
                model_node_ids[(parsed.module, symbol.name)] = node_id
                class_node_ids[(parsed.module, symbol.name)] = node_id
                model_count += 1
                nodes.append(
                    Node(
                        id=node_id,
                        type=NodeType.MODEL,
                        name=symbol.name,
                        path=relative,
                        line_start=symbol.line_start,
                        line_end=symbol.line_end,
                        metadata={
                            "decorators": symbol.decorators,
                            "signature": symbol.signature,
                            "table_name": matching_model.table_name,
                            "fields": matching_model.fields,
                            "bases": matching_model.bases,
                        },
                    )
                )
                edges.append(Edge(source=module_id, target=node_id, type=EdgeType.CONTAINS))
            elif symbol.kind == SymbolKind.COMPONENT or symbol.metadata.get("is_component"):
                node_id = f"component:{symbol.id}"
                class_node_ids[(parsed.module, symbol.name)] = node_id
                component_count += 1
                nodes.append(
                    Node(
                        id=node_id,
                        type=NodeType.COMPONENT,
                        name=symbol.name,
                        path=relative,
                        line_start=symbol.line_start,
                        line_end=symbol.line_end,
                        metadata={
                            "signature": symbol.signature,
                            **symbol.metadata,
                        },
                    )
                )
                edges.append(Edge(source=module_id, target=node_id, type=EdgeType.CONTAINS))
            else:
                kind = {
                    SymbolKind.CLASS: NodeType.CLASS,
                    SymbolKind.FUNCTION: NodeType.FUNCTION,
                    SymbolKind.METHOD: NodeType.METHOD,
                }.get(symbol.kind, NodeType.FUNCTION)
                node_id = f"symbol:{symbol.id}"
                if symbol.kind == SymbolKind.CLASS:
                    class_node_ids[(parsed.module, symbol.name)] = node_id
                symbol_count += 1
                nodes.append(
                    Node(
                        id=node_id,
                        type=kind,
                        name=symbol.name,
                        path=relative,
                        line_start=symbol.line_start,
                        line_end=symbol.line_end,
                        metadata={
                            "decorators": symbol.decorators,
                            "signature": symbol.signature,
                            **symbol.metadata,
                        },
                    )
                )
                parent_prefix = symbol.id.split(":", 1)[1] if ":" in symbol.id else symbol.id
                if "." in parent_prefix and symbol.kind == SymbolKind.METHOD:
                    parent_class = parent_prefix.split(".", 1)[0]
                    if (parsed.module, parent_class) in model_node_ids:
                        edges.append(
                            Edge(
                                source=model_node_ids[(parsed.module, parent_class)],
                                target=node_id,
                                type=EdgeType.CONTAINS,
                            )
                        )
                    elif (parsed.module, parent_class) in class_node_ids:
                        edges.append(
                            Edge(
                                source=class_node_ids[(parsed.module, parent_class)],
                                target=node_id,
                                type=EdgeType.CONTAINS,
                            )
                        )
                    else:
                        edges.append(
                            Edge(
                                source=f"symbol:{parsed.module}:{parent_class}",
                                target=node_id,
                                type=EdgeType.CONTAINS,
                            )
                        )
                else:
                    edges.append(Edge(source=module_id, target=node_id, type=EdgeType.CONTAINS))

    for (mod_name, model_name), model in models_by_module_name.items():
        source_id = model_node_ids.get((mod_name, model_name))
        if not source_id:
            continue
        for base in model.bases:
            base_simple = base.split(".")[-1]
            target_id = model_node_ids.get((mod_name, base_simple))
            if not target_id:
                candidates = models_by_name.get(base_simple, [])
                if len(candidates) == 1:
                    target_id = model_node_ids.get((candidates[0][0], base_simple))
            if target_id and target_id != source_id:
                edges.append(
                    Edge(
                        source=source_id,
                        target=target_id,
                        type=EdgeType.INHERITS,
                        metadata={"base": base, "line": model.line},
                    )
                )

    for _module_id, _relative, parsed in all_parsed:
        for rel in parsed.relationships:
            if rel.type == "inherits":
                source_sym_name = rel.source.split(":")[-1]
                source_id = class_node_ids.get(
                    (parsed.module, source_sym_name), f"symbol:{rel.source}"
                )
                target_name = rel.target.split(".")[-1]
                target_id = class_node_ids.get((parsed.module, target_name))
                if not target_id:
                    for (_mod, cls), nid in class_node_ids.items():
                        if cls == target_name:
                            target_id = nid
                            break
                if target_id and target_id != source_id:
                    edges.append(
                        Edge(
                            source=source_id,
                            target=target_id,
                            type=EdgeType.INHERITS,
                            metadata={"base": rel.target, "line": rel.line},
                        )
                    )

    for module_id, relative, _parsed, fw in python_parsed:
        for route in fw.routes:
            route_id = f"route:{route.module}:{route.method}:{route.path}"
            handler_sym = symbols_by_id.get(f"{route.module}:{route.handler}")
            line_end = handler_sym.line_end if handler_sym else route.line
            nodes.append(
                Node(
                    id=route_id,
                    type=NodeType.ROUTE,
                    name=f"{route.method} {route.path}",
                    path=relative,
                    line_start=route.line,
                    line_end=line_end,
                    metadata={
                        "method": route.method,
                        "path": route.path,
                        "handler": route.handler,
                        "tags": route.tags,
                        "response_model": route.response_model,
                    },
                )
            )
            route_count += 1
            edges.append(Edge(source=module_id, target=route_id, type=EdgeType.CONTAINS))
            if handler_sym:
                edges.append(
                    Edge(
                        source=route_id,
                        target=f"symbol:{handler_sym.id}",
                        type=EdgeType.CALLS,
                        metadata={"handler": route.handler, "line": route.line},
                    )
                )

    created_dependencies: set[str] = set()
    for module_id, relative, parsed, fw in python_parsed:
        for fw_rel in fw.relationships:
            if fw_rel.type == "depends_on":
                source_sym_id = f"symbol:{fw_rel.source}"
                target_node_id: str | None = None
                if f"{parsed.module}:{fw_rel.target}" in symbols_by_id:
                    target_node_id = f"symbol:{parsed.module}:{fw_rel.target}"
                else:
                    for imp in parsed.imports:
                        if imp.alias == fw_rel.target or imp.name == fw_rel.target:
                            if imp.level:
                                parts = parsed.module.split(".")
                                parent_parts = parts[: -imp.level]
                                target_mod = ".".join(
                                    parent_parts + ([imp.module] if imp.module else [])
                                )
                            else:
                                target_mod = imp.module
                            sym_name = imp.name or fw_rel.target
                            cand_id = f"{target_mod}:{sym_name}"
                            if cand_id in symbols_by_id:
                                target_node_id = f"symbol:{cand_id}"
                            elif target_mod in modules:
                                target_node_id = modules[target_mod]
                            else:
                                target_node_id = f"dependency:{target_mod}.{sym_name}"
                            break
                if not target_node_id:
                    target_node_id = f"dependency:{fw_rel.target}"

                if target_node_id.startswith("dependency:"):
                    dep_name = target_node_id.removeprefix("dependency:")
                    if target_node_id not in created_dependencies:
                        created_dependencies.add(target_node_id)
                        nodes.append(
                            Node(
                                id=target_node_id,
                                type=NodeType.DEPENDENCY,
                                name=dep_name,
                                path=relative,
                                line_start=fw_rel.line,
                                line_end=fw_rel.line,
                                metadata={"type": "depends", "target": fw_rel.target},
                            )
                        )
                edges.append(
                    Edge(
                        source=source_sym_id,
                        target=target_node_id,
                        type=EdgeType.DEPENDS_ON,
                        metadata={"line": fw_rel.line},
                    )
                )

            elif fw_rel.type == "includes_router":
                target_var = fw_rel.target.split(":")[-1]
                target_module_id: str | None = None
                for imp in parsed.imports:
                    if imp.alias == target_var or imp.name == target_var:
                        if imp.level:
                            parts = parsed.module.split(".")
                            parent_parts = parts[: -imp.level]
                            target_mod = ".".join(
                                parent_parts + ([imp.module] if imp.module else [])
                            )
                        else:
                            target_mod = imp.module
                        if target_mod in modules:
                            target_module_id = modules[target_mod]
                        break
                if target_module_id and target_module_id != module_id:
                    edges.append(
                        Edge(
                            source=module_id,
                            target=target_module_id,
                            type=EdgeType.USES,
                            metadata={"line": fw_rel.line, "relationship": "includes_router"},
                        )
                    )

    seen_imports: set[tuple[str, str]] = set()
    for module_id, relative, parsed in all_parsed:
        for imported in parsed.imports:
            target = modules.get(imported.module)
            if not target and imported.kind.value == "internal":
                curr_dir = Path(relative).parent
                norm_rel = os.path.normpath(str(curr_dir / imported.module)).replace("\\", "/")
                target = js_modules.get(norm_rel) or modules.get(norm_rel.replace("/", "."))
            if target and target != module_id:
                if (module_id, target) not in seen_imports:
                    seen_imports.add((module_id, target))
                    edges.append(
                        Edge(
                            source=module_id,
                            target=target,
                            type=EdgeType.IMPORTS,
                            metadata={"line": imported.line},
                        )
                    )

    return GraphDocument(
        metadata={"repository": scan.name},
        nodes=nodes,
        edges=edges,
        stats={
            "modules": len(modules),
            "symbols": symbol_count,
            "routes": route_count,
            "models": model_count,
            "components": component_count,
        },
    )
