"""Evidence-based FastAPI and ORM detection without executing target code."""

from __future__ import annotations

import ast
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class Route(BaseModel):
    model_config = ConfigDict(frozen=True)
    method: str
    path: str
    handler: str
    module: str
    line: int
    tags: list[str] = Field(default_factory=list)
    response_model: str | None = None


class DatabaseModel(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str
    module: str
    line: int
    table_name: str | None = None
    fields: list[str] = Field(default_factory=list)
    bases: list[str] = Field(default_factory=list)


class FrameworkRelationship(BaseModel):
    model_config = ConfigDict(frozen=True)
    source: str
    target: str
    type: str
    line: int


class FrameworkAnalysis(BaseModel):
    model_config = ConfigDict(frozen=True)
    routes: list[Route] = Field(default_factory=list)
    models: list[DatabaseModel] = Field(default_factory=list)
    relationships: list[FrameworkRelationship] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class FrameworkDetector:
    def detect_file(self, path: Path | str, module: str | None = None) -> FrameworkAnalysis:
        source = Path(path)
        name = module or source.with_suffix("").as_posix().replace("/", ".")
        try:
            tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        except (OSError, SyntaxError) as error:
            return FrameworkAnalysis(errors=[str(error)])
        routes: list[Route] = []
        models: list[DatabaseModel] = []
        relations: list[FrameworkRelationship] = []
        router_tags: dict[str, list[str]] = {}
        for item in ast.walk(tree):
            if (
                isinstance(item, ast.Assign)
                and isinstance(item.value, ast.Call)
                and ast.unparse(item.value.func).endswith("APIRouter")
            ):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        for keyword in item.value.keywords:
                            if keyword.arg == "tags":
                                router_tags[target.id] = ast.literal_eval(keyword.value)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    if not isinstance(decorator, ast.Call) or not isinstance(
                        decorator.func, ast.Attribute
                    ):
                        continue
                    if decorator.func.attr.lower() not in {
                        "get",
                        "post",
                        "put",
                        "patch",
                        "delete",
                        "options",
                        "head",
                    }:
                        continue
                    if (
                        not decorator.args
                        or not isinstance(decorator.args[0], ast.Constant)
                        or not isinstance(decorator.args[0].value, str)
                    ):
                        continue
                    keywords = {
                        item.arg: ast.unparse(item.value) for item in decorator.keywords if item.arg
                    }
                    tags: object = []
                    for item in decorator.keywords:
                        if item.arg == "tags":
                            tags = ast.literal_eval(item.value)
                    base_tags = router_tags.get(ast.unparse(decorator.func.value), [])
                    routes.append(
                        Route(
                            method=decorator.func.attr.upper(),
                            path=decorator.args[0].value,
                            handler=node.name,
                            module=name,
                            line=node.lineno,
                            tags=tags if isinstance(tags, list) and tags else base_tags,
                            response_model=keywords.get("response_model"),
                        )
                    )
                for call in ast.walk(node):
                    if (
                        isinstance(call, ast.Call)
                        and ast.unparse(call.func).endswith("Depends")
                        and call.args
                    ):
                        relations.append(
                            FrameworkRelationship(
                                source=f"{name}:{node.name}",
                                target=ast.unparse(call.args[0]),
                                type="depends_on",
                                line=call.lineno,
                            )
                        )
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "include_router"
                and node.args
            ):
                relations.append(
                    FrameworkRelationship(
                        source=f"{name}:{ast.unparse(node.func.value)}",
                        target=f"{name}:{ast.unparse(node.args[0])}",
                        type="includes_router",
                        line=node.lineno,
                    )
                )
            if isinstance(node, ast.ClassDef):
                bases = [ast.unparse(item) for item in node.bases]
                if node.name == "Base" or not any(
                    item.split(".")[-1] in {"Base", "SQLModel", "DeclarativeBase"} for item in bases
                ):
                    continue
                fields = [
                    item.target.id
                    for item in node.body
                    if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
                ]
                table = next(
                    (
                        ast.literal_eval(item.value)
                        for item in node.body
                        if isinstance(item, ast.Assign)
                        and any(
                            isinstance(t, ast.Name) and t.id == "__tablename__"
                            for t in item.targets
                        )
                        and isinstance(item.value, ast.Constant)
                    ),
                    None,
                )
                models.append(
                    DatabaseModel(
                        name=node.name,
                        module=name,
                        line=node.lineno,
                        table_name=table if isinstance(table, str) else None,
                        fields=fields,
                        bases=bases,
                    )
                )
        relations.sort(key=lambda item: (item.type != "includes_router", item.line))
        return FrameworkAnalysis(routes=routes, models=models, relationships=relations)
