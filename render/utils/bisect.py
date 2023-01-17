from typing import Callable, Generic, Optional, Sequence, TypeVar
from typing_extensions import Self, Protocol
import bisect


class Comparable(Protocol):

    def __lt__(self, other: Self) -> bool:
        ...

    def __gt__(self, other: Self) -> bool:
        ...

    def __le__(self, other: Self) -> bool:
        ...

    def __ge__(self, other: Self) -> bool:
        ...


T = TypeVar('T')
V = TypeVar('V', Comparable, int, float, str)


class BisectKeyWrapper(Generic[T, V]):
    """A wrapper class that allows to use a key function with bisect.
    
    Python 3.10 introduced the `key` parameter."""

    def __init__(self, obj: V, key: Callable[[T], V]) -> None:
        self.obj = obj
        self.key = key

    def __lt__(self, other: T) -> bool:
        return self.obj < self.key(other)

    def __gt__(self, other: T) -> bool:
        return self.obj > self.key(other)

    def __le__(self, other: T) -> bool:
        return self.obj <= self.key(other)

    def __ge__(self, other: T) -> bool:
        return self.obj >= self.key(other)


def find_leftmost(
    seq: Sequence[T],
    obj: V,
    key: Optional[Callable[[T], V]] = None,
) -> int:
    """Find the leftmost index of the object in the sequence."""
    wrapper = BisectKeyWrapper(obj, key) if key else obj
    return bisect.bisect_left(seq, wrapper)


def find_rightmost(
    seq: Sequence[T],
    obj: V,
    key: Optional[Callable[[T], V]] = None,
) -> int:
    """Find the rightmost index of the object in the sequence."""
    wrapper = BisectKeyWrapper(obj, key) if key else obj
    return bisect.bisect_right(seq, wrapper)
