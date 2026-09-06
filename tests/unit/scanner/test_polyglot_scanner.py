from pathlib import Path

from repolens.scanner import RepositoryScanner

POLYGLOT_FIXTURE = Path(__file__).parents[2] / "fixtures" / "scanner" / "mixed_polyglot_project"


def test_scanner_detects_polyglot_project_files() -> None:
    scan = RepositoryScanner().scan(POLYGLOT_FIXTURE)

    assert scan.name == "mixed_polyglot_project"

    # Python files discovered
    assert "backend/main.py" in scan.python_files
    assert "backend/models.py" in scan.python_files

    # JavaScript/TypeScript files discovered
    assert "frontend/src/App.tsx" in scan.javascript_files
    assert "frontend/src/components/Header.tsx" in scan.javascript_files
    assert "frontend/src/components/ItemList.tsx" in scan.javascript_files
    assert "frontend/src/utils/format.ts" in scan.javascript_files

    # Dependency manifests discovered
    assert "frontend/package.json" in scan.dependency_manifests

    # Source directories
    assert any("frontend/src" in d for d in scan.source_directories)
    assert any("backend" in d for d in scan.source_directories)


def test_scanner_handles_entrypoints() -> None:
    scan = RepositoryScanner().scan(POLYGLOT_FIXTURE)

    # In nested project structure, entrypoints are empty unless at root or named __main__.py
    assert scan.entrypoints == []
