"""Synchronize or verify packaged frontend distribution assets in backend/repolens/web/."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


def sync_assets(dist_dir: Path, web_dir: Path) -> None:
    """Copy built frontend assets from dist_dir into backend web_dir."""
    if not dist_dir.is_dir():
        raise RuntimeError(
            f"Frontend dist directory not found: {dist_dir}. Run 'npm run build' in frontend/."
        )

    web_assets = web_dir / "assets"
    if web_assets.is_dir():
        shutil.rmtree(web_assets)

    for item in dist_dir.rglob("*"):
        if item.is_file():
            rel = item.relative_to(dist_dir)
            target = web_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)

    print(f"Successfully synchronized frontend assets from {dist_dir} to {web_dir}.")


def verify_assets(dist_dir: Path, web_dir: Path) -> bool:
    """Verify packaged web assets match the current frontend build."""
    if not dist_dir.is_dir():
        print(f"Error: Frontend dist directory does not exist: {dist_dir}", file=sys.stderr)
        return False

    ignored_names = {".gitkeep", "__init__.py"}
    dist_files = {p.relative_to(dist_dir).as_posix() for p in dist_dir.rglob("*") if p.is_file()}
    web_files = {
        p.relative_to(web_dir).as_posix()
        for p in web_dir.rglob("*")
        if p.is_file() and p.name not in ignored_names
    }

    missing_in_web = dist_files - web_files
    extra_in_web = web_files - dist_files

    if missing_in_web:
        print(
            f"Error: Files present in dist/ but missing in web/: {sorted(missing_in_web)}",
            file=sys.stderr,
        )
        return False

    if extra_in_web:
        print(f"Error: Stale or extra files found in web/: {sorted(extra_in_web)}", file=sys.stderr)
        return False

    mismatched: list[str] = []
    for rel_path in sorted(dist_files):
        dist_bytes = (dist_dir / rel_path).read_bytes().replace(b"\r\n", b"\n")
        web_bytes = (web_dir / rel_path).read_bytes().replace(b"\r\n", b"\n")
        if dist_bytes != web_bytes:
            mismatched.append(rel_path)

    if mismatched:
        print(f"Error: Content mismatch in packaged web assets: {mismatched}", file=sys.stderr)
        print("Run 'python scripts/sync_web_assets.py' to update packaged assets.", file=sys.stderr)
        return False

    print(f"Verified: Packaged web assets match frontend build ({len(dist_files)} files checked).")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify that packaged web assets match frontend/dist/ without modifying files.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    dist_dir = repo_root / "frontend" / "dist"
    web_dir = repo_root / "backend" / "repolens" / "web"

    if args.check:
        if not verify_assets(dist_dir, web_dir):
            sys.exit(1)
    else:
        sync_assets(dist_dir, web_dir)


if __name__ == "__main__":
    main()
