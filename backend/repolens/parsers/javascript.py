"""JavaScript and TypeScript static analysis parser.

Parses imports, exports, classes, methods, functions, and React components
statically without importing or executing any target repository code.
"""

from __future__ import annotations

import bisect
import re
from pathlib import Path
from typing import Any

from repolens.parsers.base import BaseParser
from repolens.parsers.models import (
    Import,
    ImportKind,
    ModuleAnalysis,
    Relationship,
    Symbol,
    SymbolKind,
)

NODE_BUILTINS = frozenset(
    {
        "assert",
        "async_hooks",
        "buffer",
        "child_process",
        "cluster",
        "console",
        "constants",
        "crypto",
        "dgram",
        "diagnostics_channel",
        "dns",
        "domain",
        "events",
        "fs",
        "fs/promises",
        "http",
        "http2",
        "https",
        "inspector",
        "module",
        "net",
        "os",
        "path",
        "perf_hooks",
        "process",
        "punycode",
        "querystring",
        "readline",
        "repl",
        "stream",
        "stream/promises",
        "stream/web",
        "string_decoder",
        "timers",
        "timers/promises",
        "tls",
        "trace_events",
        "tty",
        "url",
        "util",
        "v8",
        "vm",
        "wasi",
        "worker_threads",
        "zlib",
    }
)

_REACT_HOOKS = frozenset(
    {
        "useState",
        "useEffect",
        "useContext",
        "useReducer",
        "useCallback",
        "useMemo",
        "useRef",
        "useImperativeHandle",
        "useLayoutEffect",
        "useDebugValue",
        "useDeferredValue",
        "useTransition",
        "useId",
    }
)

_REACT_CLASS_BASES = frozenset(
    {"Component", "React.Component", "PureComponent", "React.PureComponent"}
)


class JavaScriptTypeScriptParser(BaseParser):
    """Static parser for JavaScript, JSX, TypeScript, and TSX source files."""

    def parse_file(self, path: Path | str, module_path: str | None = None) -> ModuleAnalysis:
        source_path = Path(path)
        module = module_path or self._infer_module_path(source_path)
        try:
            content = source_path.read_text(encoding="utf-8")
        except OSError as error:
            return ModuleAnalysis(path=str(source_path), module=module, errors=[str(error)])
        except UnicodeDecodeError as error:
            return ModuleAnalysis(path=str(source_path), module=module, errors=[str(error)])

        return self.parse_content(content, path=str(source_path), module=module)

    def parse_content(self, content: str, *, path: str, module: str) -> ModuleAnalysis:
        line_offsets = [0] + [m.end() for m in re.finditer(r"\n", content)]

        def get_line(pos: int) -> int:
            return bisect.bisect_right(line_offsets, pos)

        masked_chars = list(content)
        jsdoc_comments: dict[int, str] = {}
        errors: list[str] = []

        n = len(content)
        i = 0
        while i < n:
            c = content[i]
            # Line comment
            if c == "/" and i + 1 < n and content[i + 1] == "/":
                while i < n and content[i] != "\n":
                    masked_chars[i] = " "
                    i += 1
                continue

            # Block comment / JSDoc
            if c == "/" and i + 1 < n and content[i + 1] == "*":
                start = i
                is_jsdoc = (
                    i + 2 < n and content[i + 2] == "*" and (i + 3 >= n or content[i + 3] != "/")
                )
                i += 2
                while i + 1 < n and not (content[i] == "*" and content[i + 1] == "/"):
                    if content[i] != "\n":
                        masked_chars[i] = " "
                    i += 1
                if i + 1 < n:
                    masked_chars[start] = " "
                    masked_chars[start + 1] = " "
                    masked_chars[i] = " "
                    masked_chars[i + 1] = " "
                    i += 2
                    end_line = get_line(i)
                    if is_jsdoc:
                        raw_comment = content[start:i]
                        cleaned = self._clean_jsdoc(raw_comment)
                        jsdoc_comments[end_line] = cleaned
                else:
                    errors.append(f"{path}:{get_line(start)}: Unterminated block comment")
                continue

            # String literals: ', ", `
            if c in ("'", '"', "`"):
                quote = c
                masked_chars[i] = " "
                i += 1
                while i < n and content[i] != quote:
                    if content[i] == "\\" and i + 1 < n:
                        if content[i] != "\n":
                            masked_chars[i] = " "
                        i += 1
                        if i < n and content[i] != "\n":
                            masked_chars[i] = " "
                        i += 1
                    else:
                        if content[i] != "\n":
                            masked_chars[i] = " "
                        i += 1
                if i < n:
                    masked_chars[i] = " "
                    i += 1
                else:
                    errors.append(f"{path}: Unterminated string literal")
                continue

            i += 1

        masked = "".join(masked_chars)

        # 1. Parse Imports
        imports = self._extract_imports(content, masked, get_line)

        # 2. Parse Classes, Methods, Functions, and React Components
        symbols, relationships = self._extract_symbols_and_relations(
            content, masked, module, get_line, jsdoc_comments
        )

        return ModuleAnalysis(
            path=path,
            module=module,
            symbols=symbols,
            imports=imports,
            relationships=relationships,
            errors=errors,
        )

    @staticmethod
    def _infer_module_path(path: Path) -> str:
        parts = list(path.parts)
        stem = path.stem
        if stem == "index" and len(parts) > 1:
            return ".".join(parts[:-1]).replace("/", ".").replace("\\", ".")
        posix = path.with_suffix("").as_posix()
        return posix.replace("/", ".").replace("\\", ".")

    @staticmethod
    def _clean_jsdoc(raw: str) -> str:
        lines = raw.strip().removeprefix("/**").removesuffix("*/").strip().splitlines()
        cleaned_lines: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("*"):
                stripped = stripped[1:].strip()
            cleaned_lines.append(stripped)
        return "\n".join(cleaned_lines).strip()

    def _determine_import_kind(self, mod_name: str) -> ImportKind:
        if mod_name.startswith((".", "/")):
            return ImportKind.INTERNAL
        if mod_name.startswith("node:") or mod_name in NODE_BUILTINS:
            return ImportKind.STANDARD_LIBRARY
        return ImportKind.THIRD_PARTY

    def _extract_imports(
        self,
        content: str,
        masked: str,
        get_line: Any,
    ) -> list[Import]:
        imports: list[Import] = []

        es6_pattern = re.compile(
            r"\bimport\s+(?:type\s+)?(?:([A-Za-z0-9_$]+)\s*(?:,\s*)?)?"
            r"(?:\*\s*as\s+([A-Za-z0-9_$]+)\s*(?:,\s*)?)?"
            r"(?:\{([^}]*)\}\s*)?"
            r"(?:from\s*)?['\"]([^'\"]+)['\"]",
            re.MULTILINE,
        )

        for match in es6_pattern.finditer(content):
            # Guard: ensure 'import' was not in comment
            if masked[match.start() : match.start() + 6] != "import":
                continue

            line = get_line(match.start())
            default_name = match.group(1)
            namespace_name = match.group(2)
            named_block = match.group(3)
            mod_path = match.group(4)
            kind = self._determine_import_kind(mod_path)

            if default_name:
                imports.append(
                    Import(
                        module=mod_path,
                        name=default_name,
                        alias=None,
                        kind=kind,
                        line=line,
                    )
                )
            if namespace_name:
                imports.append(
                    Import(
                        module=mod_path,
                        name=None,
                        alias=namespace_name,
                        kind=kind,
                        line=line,
                    )
                )
            if named_block:
                for item in named_block.split(","):
                    item = item.strip()
                    if not item:
                        continue
                    item = re.sub(r"^type\s+", "", item).strip()
                    if " as " in item:
                        orig, alias = item.split(" as ", 1)
                        imports.append(
                            Import(
                                module=mod_path,
                                name=orig.strip(),
                                alias=alias.strip(),
                                kind=kind,
                                line=line,
                            )
                        )
                    else:
                        imports.append(
                            Import(
                                module=mod_path,
                                name=item.strip(),
                                alias=None,
                                kind=kind,
                                line=line,
                            )
                        )
            if not default_name and not namespace_name and not named_block:
                imports.append(
                    Import(
                        module=mod_path,
                        name=None,
                        alias=None,
                        kind=kind,
                        line=line,
                    )
                )

        # CommonJS require() pattern
        cjs_pattern = re.compile(
            r"\b(?:const|let|var)\s+(?:([A-Za-z0-9_$]+)|\{([^}]*)\})\s*=\s*(?:await\s+)?require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
            re.MULTILINE,
        )
        for match in cjs_pattern.finditer(content):
            if masked[match.start()].isspace():
                continue

            line = get_line(match.start())
            single_var = match.group(1)
            destructured = match.group(2)
            mod_path = match.group(3)
            kind = self._determine_import_kind(mod_path)

            if single_var:
                imports.append(
                    Import(
                        module=mod_path,
                        name=None,
                        alias=single_var,
                        kind=kind,
                        line=line,
                    )
                )
            elif destructured:
                for item in destructured.split(","):
                    item = item.strip()
                    if not item:
                        continue
                    if ":" in item:
                        orig, alias = item.split(":", 1)
                        imports.append(
                            Import(
                                module=mod_path,
                                name=orig.strip(),
                                alias=alias.strip(),
                                kind=kind,
                                line=line,
                            )
                        )
                    else:
                        imports.append(
                            Import(
                                module=mod_path,
                                name=item.strip(),
                                alias=None,
                                kind=kind,
                                line=line,
                            )
                        )

        imports.sort(key=lambda x: x.line)
        return imports

    def _find_matching_brace(self, masked: str, open_brace_pos: int) -> int:
        depth = 0
        n = len(masked)
        for i in range(open_brace_pos, n):
            if masked[i] == "{":
                depth += 1
            elif masked[i] == "}":
                depth -= 1
                if depth == 0:
                    return i
        return n - 1

    def _extract_symbols_and_relations(
        self,
        content: str,
        masked: str,
        module: str,
        get_line: Any,
        jsdoc_comments: dict[int, str],
    ) -> tuple[list[Symbol], list[Relationship]]:
        symbols: list[Symbol] = []
        relationships: list[Relationship] = []

        class_spans: list[tuple[int, int, str]] = []

        # 1. Classes
        class_pattern = re.compile(
            r"\b(?:export\s+)?(?:default\s+)?class\s+([A-Za-z0-9_$]+)(?:\s+extends\s+([A-Za-z0-9_$.]+))?",
            re.MULTILINE,
        )

        for match in class_pattern.finditer(content):
            # Verify match is not inside comment
            if masked[match.start()].isspace():
                continue

            class_name = match.group(1)
            base_name = match.group(2)
            start_pos = match.start()
            start_line = get_line(start_pos)

            brace_pos = masked.find("{", match.end())
            if brace_pos == -1:
                end_pos = match.end()
                end_line = start_line
            else:
                end_pos = self._find_matching_brace(masked, brace_pos)
                end_line = get_line(end_pos)

            class_spans.append((start_pos, end_pos, class_name))

            bases = [base_name] if base_name else []
            is_component = base_name in _REACT_CLASS_BASES
            kind = SymbolKind.COMPONENT if is_component else SymbolKind.CLASS

            docstring = jsdoc_comments.get(start_line) or jsdoc_comments.get(start_line - 1)
            ident = f"{module}:{class_name}"

            class_metadata: dict[str, Any] = {"bases": bases}
            if is_component:
                class_metadata["is_component"] = True
                class_metadata["component_type"] = "class"

            symbols.append(
                Symbol(
                    id=ident,
                    kind=kind,
                    name=class_name,
                    module=module,
                    line_start=start_line,
                    line_end=end_line,
                    signature=f"class {class_name}"
                    + (f" extends {base_name}" if base_name else ""),
                    docstring=docstring,
                    bases=bases,
                    metadata=class_metadata,
                )
            )

            if base_name:
                relationships.append(
                    Relationship(
                        source=ident,
                        target=base_name,
                        type="inherits",
                        line=start_line,
                    )
                )

            if brace_pos != -1:
                class_body = content[brace_pos + 1 : end_pos]
                body_masked = masked[brace_pos + 1 : end_pos]
                self._extract_class_methods(
                    class_body,
                    body_masked,
                    brace_pos + 1,
                    module,
                    class_name,
                    get_line,
                    jsdoc_comments,
                    symbols,
                )

        # 2. Functions & React Functional Components
        # Pattern A: function declarations
        fn_pattern = re.compile(
            r"\b(?:export\s+)?(?:default\s+)?(?:async\s+)?function(?:\s*\*|\s+)\s*([A-Za-z0-9_$]+)\s*\(([^)]*)\)(?:\s*:\s*([^{]+))?\s*\{",
            re.MULTILINE,
        )

        for match in fn_pattern.finditer(content):
            if masked[match.start()].isspace():
                continue

            start_pos = match.start()
            if any(s <= start_pos <= e for s, e, _ in class_spans):
                continue

            fn_name = match.group(1)
            params = match.group(2)
            ret_type = match.group(3)
            start_line = get_line(start_pos)

            open_brace = match.end() - 1
            end_pos = self._find_matching_brace(masked, open_brace)
            end_line = get_line(end_pos)

            body_content = content[open_brace:end_pos]
            is_comp = self._is_react_component(fn_name, ret_type or "", body_content)

            kind = SymbolKind.COMPONENT if is_comp else SymbolKind.FUNCTION
            ident = f"{module}:{fn_name}"
            sig = f"{fn_name}({params.strip()})"
            if ret_type:
                sig += f": {ret_type.strip()}"

            docstring = jsdoc_comments.get(start_line) or jsdoc_comments.get(start_line - 1)
            fn_metadata: dict[str, Any] = {}
            if is_comp:
                fn_metadata["is_component"] = True
                fn_metadata["component_type"] = "functional"

            symbols.append(
                Symbol(
                    id=ident,
                    kind=kind,
                    name=fn_name,
                    module=module,
                    line_start=start_line,
                    line_end=end_line,
                    signature=sig,
                    docstring=docstring,
                    metadata=fn_metadata,
                )
            )

        # Pattern B: Arrow functions / function expressions assigned to const/let/var
        arrow_pattern = re.compile(
            r"\b(?:export\s+)?(?:const|let|var)\s+([A-Za-z0-9_$]+)\s*(?::\s*([^=]+?))?\s*=\s*(?:async\s+)?(?:\(([^)]*)\)|([A-Za-z0-9_$]+))\s*(?::\s*([^=]+?))?\s*=>",
            re.MULTILINE,
        )

        for match in arrow_pattern.finditer(content):
            if masked[match.start()].isspace():
                continue

            start_pos = match.start()
            if any(s <= start_pos <= e for s, e, _ in class_spans):
                continue

            fn_name = match.group(1)
            var_type = match.group(2)
            params_paren = match.group(3)
            param_single = match.group(4)
            ret_type = match.group(5)

            params = (params_paren if params_paren is not None else param_single or "").strip()
            start_line = get_line(start_pos)

            arrow_idx = match.end()
            rest = masked[arrow_idx:].lstrip()
            offset = len(masked[arrow_idx:]) - len(rest)
            body_start = arrow_idx + offset

            if body_start < len(masked) and masked[body_start] == "{":
                end_pos = self._find_matching_brace(masked, body_start)
                end_line = get_line(end_pos)
                body_content = content[body_start:end_pos]
            else:
                semicolon = content.find(";", arrow_idx)
                newline = content.find("\n", arrow_idx)
                if semicolon != -1 and (newline == -1 or semicolon < newline):
                    end_pos = semicolon
                elif newline != -1:
                    end_pos = newline
                else:
                    end_pos = len(content)
                end_line = get_line(end_pos)
                body_content = content[arrow_idx:end_pos]

            type_info = f"{var_type or ''} {ret_type or ''}"
            is_comp = self._is_react_component(fn_name, type_info, body_content)

            kind = SymbolKind.COMPONENT if is_comp else SymbolKind.FUNCTION
            ident = f"{module}:{fn_name}"
            sig = f"{fn_name}({params})"
            if var_type:
                sig = f"{fn_name}: {var_type.strip()}"

            docstring = jsdoc_comments.get(start_line) or jsdoc_comments.get(start_line - 1)
            arrow_metadata: dict[str, Any] = {}
            if is_comp:
                arrow_metadata["is_component"] = True
                arrow_metadata["component_type"] = "functional"

            symbols.append(
                Symbol(
                    id=ident,
                    kind=kind,
                    name=fn_name,
                    module=module,
                    line_start=start_line,
                    line_end=end_line,
                    signature=sig,
                    docstring=docstring,
                    metadata=arrow_metadata,
                )
            )

        symbols.sort(key=lambda s: (s.line_start, s.id))
        return symbols, relationships

    def _extract_class_methods(
        self,
        body: str,
        body_masked: str,
        body_offset: int,
        module: str,
        class_name: str,
        get_line: Any,
        jsdoc_comments: dict[int, str],
        symbols: list[Symbol],
    ) -> None:
        method_pattern = re.compile(
            r"\b(?:public\s+|private\s+|protected\s+)?(?:async\s+)?(?:static\s+)?(?:get\s+|set\s+)?([A-Za-z0-9_$]+)\s*\(([^)]*)\)(?:\s*:\s*([^{]+))?\s*\{",
            re.MULTILINE,
        )

        for match in method_pattern.finditer(body):
            if body_masked[match.start()].isspace():
                continue

            method_name = match.group(1)
            if method_name in {"if", "for", "while", "switch", "catch"}:
                continue

            params = match.group(2).strip()
            ret_type = match.group(3)

            method_start_abs = body_offset + match.start()
            start_line = get_line(method_start_abs)

            open_brace_idx = match.end() - 1
            end_pos_masked = self._find_matching_brace(body_masked, open_brace_idx)
            end_line = get_line(body_offset + end_pos_masked)

            ident = f"{module}:{class_name}.{method_name}"
            sig = f"{method_name}({params})"
            if ret_type:
                sig += f": {ret_type.strip()}"

            docstring = jsdoc_comments.get(start_line) or jsdoc_comments.get(start_line - 1)

            symbols.append(
                Symbol(
                    id=ident,
                    kind=SymbolKind.METHOD,
                    name=method_name,
                    module=module,
                    line_start=start_line,
                    line_end=end_line,
                    signature=sig,
                    docstring=docstring,
                    metadata={},
                )
            )

    @staticmethod
    def _is_react_component(name: str, type_annotation: str, body: str) -> bool:
        if not re.match(r"^[A-Z][a-zA-Z0-9_$]*$", name):
            return False

        if re.search(r"\b(?:React\.)?(?:FC|FunctionComponent)\b", type_annotation):
            return True

        if any(re.search(rf"\b{hook}\b", body) for hook in _REACT_HOOKS):
            return True

        if re.search(r"<[A-Za-z][A-Za-z0-9_.-]*|\/>|<\/|<[A-Za-z0-9_.-]+\s*|\bclassName\s*=", body):
            return True

        return False
