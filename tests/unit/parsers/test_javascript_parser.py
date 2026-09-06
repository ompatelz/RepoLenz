from pathlib import Path

from repolens.parsers import BaseParser, JavaScriptTypeScriptParser, PythonAstParser
from repolens.parsers.models import ImportKind, SymbolKind

FIXTURES = Path(__file__).parents[2] / "fixtures" / "parsers" / "javascript"


def test_implements_base_parser_protocol() -> None:
    js_parser = JavaScriptTypeScriptParser()
    py_parser = PythonAstParser()
    assert isinstance(js_parser, BaseParser)
    assert isinstance(py_parser, BaseParser)


def test_extracts_es6_imports_from_typescript_sample() -> None:
    parser = JavaScriptTypeScriptParser()
    analysis = parser.parse_file(FIXTURES / "sample.ts", module_path="demo.sample")

    assert analysis.errors == []
    assert len(analysis.imports) == 5

    # Check import kinds and modules
    imports_by_name = {imp.name or imp.alias: imp for imp in analysis.imports}
    assert "React" in imports_by_name
    assert imports_by_name["React"].module == "react"
    assert imports_by_name["React"].kind == ImportKind.THIRD_PARTY

    assert "useState" in imports_by_name
    assert imports_by_name["useState"].module == "react"

    assert "Button" in imports_by_name
    assert imports_by_name["Button"].module == "./Button"
    assert imports_by_name["Button"].kind == ImportKind.INTERNAL

    assert "fs" in imports_by_name
    assert imports_by_name["fs"].module == "node:fs"
    assert imports_by_name["fs"].kind == ImportKind.STANDARD_LIBRARY


def test_extracts_commonjs_imports_from_javascript_sample() -> None:
    parser = JavaScriptTypeScriptParser()
    analysis = parser.parse_file(FIXTURES / "sample.js", module_path="demo.sample_js")

    assert analysis.errors == []
    assert len(analysis.imports) == 2
    assert analysis.imports[0].alias == "path"
    assert analysis.imports[0].kind == ImportKind.STANDARD_LIBRARY
    assert analysis.imports[1].alias == "fs"
    assert analysis.imports[1].kind == ImportKind.STANDARD_LIBRARY


def test_extracts_classes_methods_and_inheritance() -> None:
    parser = JavaScriptTypeScriptParser()
    analysis = parser.parse_file(FIXTURES / "sample.ts", module_path="demo.sample")

    symbols_by_name = {s.name: s for s in analysis.symbols}

    assert "BaseService" in symbols_by_name
    assert symbols_by_name["BaseService"].kind == SymbolKind.CLASS
    assert "initialize" in symbols_by_name
    assert symbols_by_name["initialize"].kind == SymbolKind.METHOD

    assert "AuthService" in symbols_by_name
    auth_service = symbols_by_name["AuthService"]
    assert auth_service.kind == SymbolKind.CLASS
    assert auth_service.bases == ["BaseService"]
    assert "login" in symbols_by_name
    assert "logout" in symbols_by_name
    assert symbols_by_name["login"].kind == SymbolKind.METHOD
    assert symbols_by_name["logout"].kind == SymbolKind.METHOD

    # Check inheritance relationship
    assert len(analysis.relationships) == 1
    rel = analysis.relationships[0]
    assert rel.type == "inherits"
    assert rel.source == "demo.sample:AuthService"
    assert rel.target == "BaseService"


def test_extracts_functions_and_react_components() -> None:
    parser = JavaScriptTypeScriptParser()
    analysis = parser.parse_file(FIXTURES / "sample.ts", module_path="demo.sample")

    symbols_by_name = {s.name: s for s in analysis.symbols}

    assert "formatName" in symbols_by_name
    assert symbols_by_name["formatName"].kind == SymbolKind.FUNCTION

    assert "isAdmin" in symbols_by_name
    assert symbols_by_name["isAdmin"].kind == SymbolKind.FUNCTION

    assert "UserCard" in symbols_by_name
    user_card = symbols_by_name["UserCard"]
    assert user_card.kind == SymbolKind.COMPONENT
    assert user_card.metadata.get("is_component") is True
    assert user_card.metadata.get("component_type") == "functional"
    assert user_card.docstring is not None
    assert "user card" in user_card.docstring.lower()


def test_extracts_javascript_classes_and_methods() -> None:
    parser = JavaScriptTypeScriptParser()
    analysis = parser.parse_file(FIXTURES / "sample.js", module_path="demo.sample_js")

    symbols_by_name = {s.name: s for s in analysis.symbols}
    assert "EventEmitter" in symbols_by_name
    assert symbols_by_name["EventEmitter"].kind == SymbolKind.CLASS
    assert "constructor" in symbols_by_name
    assert "on" in symbols_by_name
    assert "emit" in symbols_by_name
    assert "helper" in symbols_by_name
    assert "toUpper" in symbols_by_name


def test_graceful_handling_of_malformed_syntax() -> None:
    parser = JavaScriptTypeScriptParser()
    analysis = parser.parse_file(FIXTURES / "malformed.ts", module_path="demo.malformed")

    # Does not crash or raise an unhandled exception
    assert len(analysis.errors) > 0
    assert analysis.symbols == []
