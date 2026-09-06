"""Generate synthetic multi-package Python repositories for performance benchmarking."""

from __future__ import annotations

import argparse
from pathlib import Path


def generate_synthetic_repo(
    target_dir: Path,
    num_packages: int = 10,
    modules_per_package: int = 10,
    include_cycles: bool = True,
) -> dict[str, int]:
    """Generate a realistic static repository structure with routes, models, and dependencies."""
    target_dir.mkdir(parents=True, exist_ok=True)
    src_dir = target_dir / "src"
    src_dir.mkdir(exist_ok=True)

    # Project metadata
    (target_dir / "pyproject.toml").write_text(
        '[project]\nname = "synthetic-large-app"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    (target_dir / ".gitignore").write_text("__pycache__/\n*.pyc\n.venv/\n", encoding="utf-8")

    total_modules = 0
    total_classes = 0
    total_functions = 0
    total_routes = 0
    total_models = 0

    for p_idx in range(num_packages):
        pkg_name = f"pkg_{p_idx}"
        pkg_dir = src_dir / pkg_name
        pkg_dir.mkdir(exist_ok=True)
        (pkg_dir / "__init__.py").write_text(f'"""Package {pkg_name}."""\n', encoding="utf-8")
        total_modules += 1

        for m_idx in range(modules_per_package):
            mod_name = f"module_{m_idx}"
            mod_file = pkg_dir / f"{mod_name}.py"

            # Create intra-package and cross-package import targets
            imports: list[str] = ["from __future__ import annotations", "from typing import Any"]
            if m_idx > 0:
                imports.append(f"from {pkg_name}.module_{m_idx - 1} import Service_{m_idx - 1}")
            if p_idx > 0 and m_idx == 0:
                imports.append(f"from pkg_{p_idx - 1}.module_0 import Service_0")

            # Controlled cycle between pkg_0 and pkg_1 if enabled
            if include_cycles and p_idx == 1 and m_idx == 1:
                imports.append("from pkg_0.module_1 import Helper_1")

            code_lines = [
                *imports,
                "",
                f'"""Module {mod_name} in package {pkg_name}."""',
                "",
                f"class Model_{m_idx}(Base):",
                f'    """SQLAlchemy model {m_idx}."""',
                f'    __tablename__ = "table_{p_idx}_{m_idx}"',
                "    id: int",
                "    name: str",
                "",
                f"class Service_{m_idx}:",
                f'    """Service class {m_idx}."""',
                "    def __init__(self) -> None:",
                "        self.active = True",
                "",
                f"    def process_{m_idx}(self, data: Any) -> Any:",
                f'        """Process action {m_idx}."""',
                "        return data",
                "",
                f"@router.get('/api/v1/{pkg_name}/{mod_name}')",
                f"def get_{pkg_name}_{mod_name}() -> dict[str, str]:",
                f'    """FastAPI route handler for {pkg_name}/{mod_name}."""',
                f'    return {{"status": "ok", "module": "{mod_name}"}}',
                "",
                f"def compute_{m_idx}(value: int) -> int:",
                f'    """Pure compute helper {m_idx}."""',
                f"    return value * {m_idx + 1}",
                "",
            ]

            if include_cycles and p_idx == 0 and m_idx == 1:
                code_lines.extend(
                    [
                        "from pkg_1.module_1 import Service_1",
                        "class Helper_1:",
                        "    def help(self) -> None:",
                        "        Service_1()",
                        "",
                    ]
                )

            mod_file.write_text("\n".join(code_lines), encoding="utf-8")
            total_modules += 1
            total_classes += 2
            total_functions += 2
            total_routes += 1
            total_models += 1

    return {
        "packages": num_packages,
        "modules": total_modules,
        "classes": total_classes,
        "functions": total_functions,
        "routes": total_routes,
        "models": total_models,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(".tmp_benchmark_repo"),
        help="Destination directory for synthetic repository.",
    )
    parser.add_argument("--packages", type=int, default=10, help="Number of packages.")
    parser.add_argument(
        "--modules-per-package", type=int, default=10, help="Number of modules per package."
    )
    args = parser.parse_args()

    stats = generate_synthetic_repo(
        args.output,
        num_packages=args.packages,
        modules_per_package=args.modules_per_package,
    )
    print(f"Generated synthetic repository at {args.output}: {stats}")


if __name__ == "__main__":
    main()
