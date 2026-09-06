from collections.abc import Callable


class PlainHelper:
    def get(self, key: str) -> str:
        return key


class NotAnOrmModel:
    name: str
    age: int


def not_a_route() -> None:
    pass


class FakeDecorator:
    @staticmethod
    def get(val: int) -> Callable[[Callable[[], int]], Callable[[], int]]:
        def inner(fn: Callable[[], int]) -> Callable[[], int]:
            return fn

        return inner


@FakeDecorator.get(42)
def decorated_with_int() -> int:
    return 42


def func_with_default(arg: str = "default") -> str:
    return arg
