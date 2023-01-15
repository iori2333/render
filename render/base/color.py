from typing_extensions import Self
from typing import Tuple


class Color:

    def __init__(self, r: int, g: int, b: int, a: int) -> None:
        self.r = r
        self.g = g
        self.b = b
        self.a = a

    @classmethod
    def from_color(cls, color: Self, opacity: float) -> Self:
        return cls(*color.to_rgb(), int(opacity * 255))

    @classmethod
    def of(cls, r: int, g: int, b: int, a: int = 255) -> Self:
        return cls(r, g, b, a)

    @classmethod
    def of_hex(cls, hex: str) -> Self:
        hex = hex.lstrip("#")
        return cls(*tuple(int(hex[i:i + 2], 16) for i in (0, 2, 4)))

    def as_tuple(self) -> Tuple[int, int, int, int]:
        return self.r, self.g, self.b, self.a

    def to_rgb(self) -> Tuple[int, int, int]:
        return self.r, self.g, self.b


class Palette:
    TRANSPARENT = Color.of(255, 255, 255, 0)
    WHITE = Color.of(255, 255, 255)
    BLACK = Color.of(0, 0, 0)
    RED = Color.of(255, 0, 0)
    GREEN = Color.of(0, 255, 0)
    BLUE = Color.of(0, 0, 255)
