from pathlib import Path

import pytest

from repolens.scanner import RepositoryScanner

FIXTURES = Path(__file__).parents[2] / "fixtures" / "scanner"


def scan_fixture(name: str):
    return RepositoryScanner().scan(FIXTURES / name)


def test_scans_a_simple_python_project() -> None:
    scan = scan_fixture("simple_python_project")

    assert scan.name == "simple_python_project"
    assert Path(scan.root) == FIXTURES / "simple_python_project"
    assert scan.files == [
        "README.md",
        "main.py",
        "pyproject.toml",
        "simple_package/__init__.py",
        "simple_package/service.py",
    ]
    assert scan.directories == ["simple_package"]
    assert scan.python_files == [
        "main.py",
        "simple_package/__init__.py",
        "simple_package/service.py",
    ]
    assert scan.packages == ["simple_package"]
    assert scan.readme == "README.md"
    assert scan.gitignore is None
    assert scan.dependency_manifests == ["pyproject.toml"]
    assert scan.entrypoints == ["main.py"]


def test_scans_nested_packages_and_repository_metadata() -> None:
    scan = scan_fixture("nested_python_project")

    assert scan.packages == ["src/demo", "src/demo/tools"]
    assert scan.tests == ["tests/test_cli.py"]
    assert scan.configuration_files == [".ruff.toml", "pyproject.toml"]
    assert scan.dependency_manifests == ["pyproject.toml", "requirements-dev.txt"]
    assert scan.entrypoints == ["src/demo/__main__.py"]
    assert scan.source_directories == ["src"]
    assert all("\\" not in path for path in scan.files)


def test_excludes_ignored_and_tool_generated_content() -> None:
    scan = scan_fixture("ignored_content_project")

    assert scan.gitignore == ".gitignore"
    assert scan.files == [
        ".gitignore",
        "README.md",
        "app/__init__.py",
        "app/main.py",
        "pyproject.toml",
    ]
    assert scan.directories == ["app"]
    assert scan.python_files == ["app/__init__.py", "app/main.py"]
    assert "generated/output.py" not in scan.files
    assert "app/settings.local.py" not in scan.files
    assert not any(
        path.startswith((".git/", ".venv/", "build/", "__pycache__/", ".repolens/"))
        for path in scan.files
    )


def test_scans_an_empty_directory(tmp_path: Path) -> None:
    empty_repository = tmp_path / "empty-repository"
    empty_repository.mkdir()

    scan = RepositoryScanner().scan(empty_repository)

    assert scan.name == "empty-repository"
    assert Path(scan.root) == empty_repository
    assert scan.files == []
    assert scan.directories == []
    assert scan.python_files == []
    assert scan.packages == []
    assert scan.tests == []
    assert scan.readme is None
    assert scan.gitignore is None
    assert scan.dependency_manifests == []
    assert scan.configuration_files == []
    assert scan.entrypoints == []
    assert scan.source_directories == []


@pytest.mark.parametrize(
    "path_factory",
    [
        lambda path: path.as_posix(),
        lambda path: str(path),
    ],
    ids=["posix-path-string", "windows-path-string"],
)
def test_accepts_string_paths_in_native_and_windows_notation(path_factory) -> None:
    root = FIXTURES / "simple_python_project"

    scan = RepositoryScanner().scan(path_factory(root))

    assert scan.name == "simple_python_project"
    assert scan.files == [
        "README.md",
        "main.py",
        "pyproject.toml",
        "simple_package/__init__.py",
        "simple_package/service.py",
    ]
