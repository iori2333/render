from __future__ import annotations

from typing_extensions import Self

from render import Color, Image, Palette


class TestRect(Image):

    @classmethod
    def of(cls, width: int, height: int, color: Color | None) -> Self:
        return cls.from_color(width, height, color or Palette.TRANSPARENT)


__all__ = ['TestRect']
