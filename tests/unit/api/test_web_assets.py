from pathlib import Path

from fastapi.testclient import TestClient
from scripts.sync_web_assets import sync_assets, verify_assets

from repolens.api import create_app
from repolens.models import GraphDocument


def test_local_api_serves_packaged_web_app() -> None:
    response = TestClient(create_app(GraphDocument())).get("/")

    assert response.status_code == 200
    assert "RepoLens" in response.text


def test_verify_assets_succeeds_when_in_sync(tmp_path: Path) -> None:
    dist_dir = tmp_path / "dist"
    web_dir = tmp_path / "web"
    dist_dir.mkdir()
    (dist_dir / "index.html").write_text("<html>app</html>", encoding="utf-8")
    (dist_dir / "assets").mkdir()
    (dist_dir / "assets" / "app.js").write_text("console.log('test')", encoding="utf-8")

    sync_assets(dist_dir, web_dir)
    assert verify_assets(dist_dir, web_dir) is True


def test_verify_assets_detects_mismatch(tmp_path: Path) -> None:
    dist_dir = tmp_path / "dist"
    web_dir = tmp_path / "web"
    dist_dir.mkdir()
    (dist_dir / "index.html").write_text("<html>v1</html>", encoding="utf-8")
    sync_assets(dist_dir, web_dir)

    # Modify dist without syncing
    (dist_dir / "index.html").write_text("<html>v2</html>", encoding="utf-8")
    assert verify_assets(dist_dir, web_dir) is False


def test_verify_assets_detects_extra_file(tmp_path: Path) -> None:
    dist_dir = tmp_path / "dist"
    web_dir = tmp_path / "web"
    dist_dir.mkdir()
    (dist_dir / "index.html").write_text("<html>app</html>", encoding="utf-8")
    sync_assets(dist_dir, web_dir)

    # Add extra stale file to web_dir
    (web_dir / "stale.js").write_text("old", encoding="utf-8")
    assert verify_assets(dist_dir, web_dir) is False
