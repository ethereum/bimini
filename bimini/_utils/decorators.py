import functools
from typing import (
    Iterable,
    Callable,
    Tuple,
    TypeVar,
)


T = TypeVar('T')


def to_tuple(fn: Callable[..., Iterable[T]]) -> Callable[..., Tuple[T, ...]]:
    @functools.wraps(fn)
    def inner(*args, **kwargs) -> Tuple[T, ...]:  # type: ignore
        return tuple(fn(*args, **kwargs))
    return inner
