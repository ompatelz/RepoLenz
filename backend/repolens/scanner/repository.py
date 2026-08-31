"""Safe filesystem discovery for repositories supplied to RepoLens."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pathspec

from repolens.scanner.models import RepositoryScan

_DEFAULT_IGNORED_DIRECTORIES = frozenset(
    {
        ".git",
        "node_modules",
        "venv",
        ".venv",
        "__pycache__",
        "dist",
        "build",
        "coverage",
        ".pytest_cache",
        ".mypy_cache",
    }
)
_DEPENDENCY_MANIFESTS = frozenset(
    {
        "pyproject.toml",
        "requirements.txt",
        "setup.py",
        "setup.cfg",
        "Pipfile",
        "poetry.lock",
        "package.json",
    }
)
_CONFIGURATION_FILES = frozenset(
    {
        ".env.example",
        ".ruff.toml",
        "Dockerfile",
        "docker-compose.yml",
        "docker-compose.yaml",
        "pyproject.toml",
    }
)
_ENTRYPOINT_NAMES = frozenset({"__main__.py", "main.py", "app.py", "cli.py", "manage.py"})
_SOURCE_DIRECTORY_NAMES = frozenset({"src", "app", "backend", "lib"})


class RepositoryScanner:
    """Create a static inventory of a repository without importing its contents."""

    def scan(self, path: Path | str) -> RepositoryScan:
        root = Path(path).expanduser().resolve(strict=True)
        if not root.is_dir():
            msg = f"Repository path is not a directory: {root}"
            raise NotADirectoryError(msg)

        ignored = self._ignored_paths(root)
        files: list[str] = []
        directories: list[str] = []

        for current_root, directory_names, file_names in self._walk(root, ignored):
            current_path = Path(current_root)
            for directory_name in directory_names:
                directories.append(self._relative(current_path / directory_name, root))
            for file_name in file_names:
                files.append(self._relative(current_path / file_name, root))

        files.sort()
        directories.sort()
        python_files = [item for item in files if item.endswith(".py")]
        package_markers = {
            item for item in python_files if item == "__init__.py" or item.endswith("/__init__.py")
        }
        packages = sorted(
            "." if item == "__init__.py" else item.removesuffix("/__init__.py")
            for item in package_markers
        )

        return RepositoryScan(
            root=str(root),
            name=root.name,
            files=files,
            directories=directories,
            python_files=python_files,
            packages=packages,
            tests=[item for item in python_files if self._is_test_file(item)],
            source_directories=[
                item for item in directories if Path(item).name in _SOURCE_DIRECTORY_NAMES
            ],
            dependency_manifests=[
                item
                for item in files
                if Path(item).name in _DEPENDENCY_MANIFESTS
                or Path(item).name.startswith("requirements")
                and Path(item).suffix == ".txt"
            ],
            configuration_files=[item for item in files if Path(item).name in _CONFIGURATION_FILES],
            entrypoints=[item for item in python_files if self._is_entrypoint(item)],
            readme=next(
                (item for item in files if Path(item).name.lower().startswith("readme")), None
            ),
            gitignore=".gitignore" if ".gitignore" in files else None,
        )

    @staticmethod
    def _relative(path: Path, root: Path) -> str:
        return path.relative_to(root).as_posix()

    def _walk(
        self,
        root: Path,
        ignored: pathspec.PathSpec,
    ) -> Iterator[tuple[str, list[str], list[str]]]:
        for current_root, directory_names, file_names in os.walk(
            root, topdown=True, followlinks=False
        ):
            current_path = Path(current_root)
            directory_names[:] = [
                name
                for name in directory_names
                if not self._should_ignore(current_path / name, root, ignored)
            ]
            file_names[:] = [
                name
                for name in file_names
                if not self._should_ignore(current_path / name, root, ignored)
            ]
            yield current_root, directory_names, file_names

    def _ignored_paths(self, root: Path) -> pathspec.PathSpec:
        gitignore = root / ".gitignore"
        lines = gitignore.read_text(encoding="utf-8").splitlines() if gitignore.is_file() else []
        return pathspec.GitIgnoreSpec.from_lines(lines)

    def _should_ignore(
        self,
        candidate: Path,
        root: Path,
        ignored: pathspec.PathSpec,
    ) -> bool:
        relative = self._relative(candidate, root)
        match_path = f"{relative}/" if candidate.is_dir() else relative
        return candidate.name in _DEFAULT_IGNORED_DIRECTORIES or ignored.match_file(match_path)

    @staticmethod
    def _is_test_file(relative_path: str) -> bool:
        path = Path(relative_path)
        return (
            "tests" in path.parts or path.name.startswith("test_") or path.name.endswith("_test.py")
        )

    @staticmethod
    def _is_entrypoint(relative_path: str) -> bool:
        path = Path(relative_path)
        if path.name == "__main__.py":
            return True
        return len(path.parts) == 1 and path.name in _ENTRYPOINT_NAMES
