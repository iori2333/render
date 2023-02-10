from __future__ import annotations

from contextlib import contextmanager
from typing_extensions import Self

from render import Color, Image, Palette


class TestRect(Image):

    @classmethod
    def of(cls, width: int, height: int, color: Color | None) -> Self:
        return cls.from_color(width, height, color or Palette.TRANSPARENT)


@contextmanager
def assert_raises(exception: type[BaseException], verbose: bool = False):
    try:
        yield
    except exception as e:
        if verbose:
            print(f"raised: {e!r}")
    else:
        raise AssertionError(f"Expected {exception.__name__} to be raised.")


__all__ = [
    "TestRect",
    "assert_raises",
]
