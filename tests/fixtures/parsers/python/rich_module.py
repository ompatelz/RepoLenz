"""A deliberately varied module used to validate Python AST extraction."""

import asyncio
import json as json_module
from collections import defaultdict as DefaultDict
from . import helpers
from ..shared.models import BaseRecord as Record


@register("service")
@instrumented
class UserService(Record, Mixin):
    """Coordinates user-facing work."""

    def __init__(self, client: Client) -> None:
        self.client = client

    @classmethod
    def from_config(cls, config: Config) -> "UserService":
        return cls(Client(config))

    @timed
    async def fetch_user(self, user_id: str) -> User:
        response = await self.client.fetch(user_id)
        return User.from_response(response)


@public
def build_index(records: list[Record]) -> DefaultDict[str, list[Record]]:
    index: DefaultDict[str, list[Record]] = DefaultDict(list)
    for record in records:
        index[record.kind].append(record)
    return index


async def refresh_cache(service: UserService, user_id: str) -> None:
    await service.fetch_user(user_id)
    await asyncio.sleep(0)
