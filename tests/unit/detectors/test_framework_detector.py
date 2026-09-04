from pathlib import Path

from repolens.detectors.frameworks import FrameworkDetector

FIXTURES = Path(__file__).parents[2] / "fixtures" / "detectors" / "frameworks"


def detect(name: str, module: str):
    return FrameworkDetector().detect_file(FIXTURES / name, module)


def test_detects_fastapi_app_and_router_routes_with_metadata() -> None:
    analysis = detect("fastapi_routes.py", "demo.api.routes")

    assert [
        (route.method, route.path, route.handler, route.module, route.tags, route.response_model)
        for route in analysis.routes
    ] == [
        ("GET", "/health", "health_check", "demo.api.routes", ["system"], "HealthResponse"),
        ("GET", "/{user_id}", "get_user", "demo.api.routes", ["users"], "UserResponse"),
    ]
    assert all(route.line > 0 for route in analysis.routes)


def test_detects_router_inclusion_and_depends_relationships_with_evidence() -> None:
    analysis = detect("fastapi_routes.py", "demo.api.routes")

    assert [
        (relation.source, relation.target, relation.type, relation.line)
        for relation in analysis.relationships
    ] == [
        ("demo.api.routes:app", "demo.api.routes:users_router", "includes_router", 22),
        ("demo.api.routes:get_user", "get_service", "depends_on", 18),
    ]


def test_detects_sqlalchemy_and_sqlmodel_models_and_annotated_fields() -> None:
    analysis = detect("orm_models.py", "demo.data.models")

    assert [
        (model.name, model.module, model.table_name, model.bases, model.fields)
        for model in analysis.models
    ] == [
        (
            "User",
            "demo.data.models",
            "users",
            ["Base"],
            ["id", "email", "posts"],
        ),
        (
            "Post",
            "demo.data.models",
            "posts",
            ["Base"],
            ["id", "author_id", "author"],
        ),
        (
            "AuditEntry",
            "demo.data.models",
            None,
            ["SQLModel"],
            ["id", "event"],
        ),
    ]
    assert all(model.line > 0 for model in analysis.models)


def test_returns_errors_for_malformed_framework_files_without_raising(tmp_path: Path) -> None:
    malformed = tmp_path / "broken.py"
    malformed.write_text('@app.get("/oops")\ndef broken(:\n', encoding="utf-8")

    analysis = FrameworkDetector().detect_file(malformed, "demo.broken")

    assert analysis.routes == []
    assert analysis.models == []
    assert analysis.relationships == []
    assert len(analysis.errors) == 1
    assert "broken.py" in analysis.errors[0]
