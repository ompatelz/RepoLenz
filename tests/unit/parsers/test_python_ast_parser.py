from pathlib import Path

from repolens.parsers import PythonAstParser

FIXTURES = Path(__file__).parents[2] / "fixtures" / "parsers" / "python"


def parse_fixture(name: str):
    return PythonAstParser().parse_file(FIXTURES / name, module_path=f"demo.{name[:-3]}")


def test_extracts_imports_and_preserves_aliases_and_relative_levels() -> None:
    analysis = parse_fixture("rich_module.py")

    assert [
        (item.module, item.name, item.alias, item.level, item.kind) for item in analysis.imports
    ] == [
        ("asyncio", None, None, 0, "standard_library"),
        ("json", None, "json_module", 0, "standard_library"),
        ("collections", "defaultdict", "DefaultDict", 0, "standard_library"),
        ("", "helpers", None, 1, "unresolved"),
        ("shared.models", "BaseRecord", "Record", 2, "unresolved"),
    ]
    assert [item.line for item in analysis.imports] == [3, 4, 5, 6, 7]


def test_extracts_classes_methods_functions_and_decorators() -> None:
    analysis = parse_fixture("rich_module.py")

    assert [(item.id, item.name, item.kind, item.module) for item in analysis.symbols] == [
        ("demo.rich_module:UserService", "UserService", "class", "demo.rich_module"),
        ("demo.rich_module:UserService.__init__", "__init__", "method", "demo.rich_module"),
        ("demo.rich_module:UserService.from_config", "from_config", "method", "demo.rich_module"),
        ("demo.rich_module:UserService.fetch_user", "fetch_user", "method", "demo.rich_module"),
        ("demo.rich_module:build_index", "build_index", "function", "demo.rich_module"),
        ("demo.rich_module:refresh_cache", "refresh_cache", "function", "demo.rich_module"),
    ]

    user_service = analysis.symbols[0]
    assert user_service.decorators == ["register('service')", "instrumented"]
    assert user_service.bases == ["Record", "Mixin"]
    assert analysis.symbols[2].decorators == ["classmethod"]
    assert analysis.symbols[3].decorators == ["timed"]
    assert analysis.symbols[4].decorators == ["public"]


def test_extracts_inheritance_relationships_with_evidence() -> None:
    analysis = parse_fixture("rich_module.py")

    assert [(item.type, item.source, item.target) for item in analysis.relationships] == [
        ("inherits", "demo.rich_module:UserService", "Record"),
        ("inherits", "demo.rich_module:UserService", "Mixin"),
    ]
    assert all(item.line >= 1 for item in analysis.relationships)


def test_reports_syntax_errors_without_raising() -> None:
    analysis = parse_fixture("malformed_module.py")

    assert analysis.imports == []
    assert analysis.symbols == []
    assert analysis.relationships == []
    assert len(analysis.errors) == 1
    assert "malformed_module.py" in analysis.errors[0]
