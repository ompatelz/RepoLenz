class UserService:
    def list_all(self) -> list[dict[str, str]]:
        return [{"id": "1", "name": "Alice"}]

    def create(self, data: dict[str, str]) -> dict[str, str]:
        return data
