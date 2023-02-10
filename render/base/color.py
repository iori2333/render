from __future__ import annotations

try:
    from mixbox import lerp
except ImportError as e:
    from warnings import warn
    warn("natural_blend requires pymixbox to be installed, "
         "using linear blend as fallback.")
    lerp = None

from random import randint
from typing import Generator, NamedTuple

from typing_extensions import Self


class Color(NamedTuple):

    r: int
    g: int
    b: int
    a: int

    @classmethod
    def from_color(cls, color: Self, opacity: float | int = 1.0) -> Self:
        return cls.of(*color.to_rgb(), opacity)

    @classmethod
    def of(cls, r: int, g: int, b: int, a: int | float = 255) -> Self:
        if isinstance(a, float):
            a = int(a * 255)
        return cls(r, g, b, a)

    @classmethod
    def of_hex(cls, hex: str, opacity: float | int = 1.0) -> Self:
        hex = hex.lstrip("#")
        r, g, b = (int(hex[i:i + 2], 16) for i in (0, 2, 4))
        return cls.of(r, g, b, opacity)

    @classmethod
    def rand(cls, rand_alpha: bool = False) -> Self:
        r, g, b, a = (randint(0, 255) for _ in range(4))
        return cls.of(r, g, b, a if rand_alpha else 255)

    def of_alpha(self, a: int | float) -> Self:
        return self.of(self.r, self.g, self.b, a)

    def as_hex(self, lower: bool = False) -> str:
        if lower:
            return f"#{self.r:02x}{self.g:02x}{self.b:02x}"
        return f"#{self.r:02X}{self.g:02X}{self.b:02X}"

    def to_rgb(self) -> tuple[int, int, int]:
        return self.r, self.g, self.b

    def __repr__(self) -> str:
        return f"Color(r={self.r}, g={self.g}, b={self.b}, a={self.a})"

    def __str__(self) -> str:
        return self.as_hex()


class Palette:
    # yapf: disable
    TRANSPARENT             = Color.of(255, 255, 255, 0)
    # Basic colors
    BLACK                   = Color.of(0, 0, 0)
    SILVER                  = Color.of(192, 192, 192)
    GRAY                    = Color.of(128, 128, 128)
    WHITE                   = Color.of(255, 255, 255)
    RED                     = Color.of(255, 0, 0)
    PURPLE                  = Color.of(128, 0, 128)
    FUCHSIA                 = Color.of(255, 0, 255)
    GREEN                   = Color.of(0, 255, 0)
    LIME                    = Color.of(0, 255, 0)
    OLIVE                   = Color.of(128, 128, 0)
    YELLOW                  = Color.of(255, 255, 0)
    NAVY                    = Color.of(0, 0, 128)
    BLUE                    = Color.of(0, 0, 255)
    TEAL                    = Color.of(0, 128, 128)
    AQUA                    = Color.of(0, 255, 255)
    # Extended Colors
    ALICE_BLUE              = Color.of(240, 248, 255)
    ANTIQUE_WHITE           = Color.of(250, 235, 215)
    AQUA_MARINE             = Color.of(127, 255, 212)
    AZURE                   = Color.of(240, 255, 255)
    BEIGE                   = Color.of(245, 245, 220)
    BISQUE                  = Color.of(255, 228, 196)
    BLANCHED_ALMOND         = Color.of(255, 235, 205)
    BLUE_VIOLET             = Color.of(138, 43, 226)
    BROWN                   = Color.of(165, 42, 42)
    BURLY_WOOD              = Color.of(222, 184, 135)
    CADET_BLUE              = Color.of(95, 158, 160)
    CHARTREUSE              = Color.of(127, 255, 0)
    CHOCOLATE               = Color.of(210, 105, 30)
    CORAL                   = Color.of(255, 127, 80)
    CORNFLOWER_BLUE         = Color.of(100, 149, 237)
    CORNSILK                = Color.of(255, 248, 220)
    CRIMSON                 = Color.of(220, 20, 60)
    CYAN                    = Color.of(0, 255, 255)
    DARK_BLUE               = Color.of(0, 0, 139)
    DARK_CYAN               = Color.of(0, 139, 139)
    DARK_GOLDEN_ROD         = Color.of(184, 134, 11)
    DARK_GRAY               = Color.of(169, 169, 169)
    DARK_GREEN              = Color.of(0, 100, 0)
    DARK_KHAKI              = Color.of(189, 183, 107)
    DARK_MAGENTA            = Color.of(139, 0, 139)
    DARK_OLIVE_GREEN        = Color.of(85, 107, 47)
    DARK_ORANGE             = Color.of(255, 140, 0)
    DARK_ORCHID             = Color.of(153, 50, 204)
    DARK_RED                = Color.of(139, 0, 0)
    DARK_SALMON             = Color.of(233, 150, 122)
    DARK_SEA_GREEN          = Color.of(143, 188, 143)
    DARK_SLATE_BLUE         = Color.of(72, 61, 139)
    DARK_SLATE_GRAY         = Color.of(47, 79, 79)
    DARK_TURQUOISE          = Color.of(0, 206, 209)
    DARK_VIOLET             = Color.of(148, 0, 211)
    DEEP_PINK               = Color.of(255, 20, 147)
    DEEP_SKY_BLUE           = Color.of(0, 191, 255)
    DIM_GRAY                = Color.of(105, 105, 105)
    DODGER_BLUE             = Color.of(30, 144, 255)
    FIRE_BRICK              = Color.of(178, 34, 34)
    FLORAL_WHITE            = Color.of(255, 250, 240)
    FOREST_GREEN            = Color.of(34, 139, 34)
    GAINSBORO               = Color.of(220, 220, 220)
    GHOST_WHITE             = Color.of(248, 248, 255)
    GOLD                    = Color.of(255, 215, 0)
    GOLDEN_ROD              = Color.of(218, 165, 32)
    GREEN_YELLOW            = Color.of(173, 255, 47)
    HONEY_DEW               = Color.of(240, 255, 240)
    HOT_PINK                = Color.of(255, 105, 180)
    INDIAN_RED              = Color.of(205, 92, 92)
    INDIGO                  = Color.of(75, 0, 130)
    IVORY                   = Color.of(255, 255, 240)
    KHAKI                   = Color.of(240, 230, 140)
    LAVENDER                = Color.of(230, 230, 250)
    LAVENDER_BLUSH          = Color.of(255, 240, 245)
    LAWN_GREEN              = Color.of(124, 252, 0)
    LEMON_CHIFFON           = Color.of(255, 250, 205)
    LIGHT_BLUE              = Color.of(173, 216, 230)
    LIGHT_CORAL             = Color.of(240, 128, 128)
    LIGHT_CYAN              = Color.of(224, 255, 255)
    LIGHT_GOLDEN_ROD_YELLOW = Color.of(250, 250, 210)
    LIGHT_GRAY              = Color.of(211, 211, 211)
    LIGHT_GREEN             = Color.of(144, 238, 144)
    LIGHT_PINK              = Color.of(255, 182, 193)
    LIGHT_SALMON            = Color.of(255, 160, 122)
    LIGHT_SEA_GREEN         = Color.of(32, 178, 170)
    LIGHT_SKY_BLUE          = Color.of(135, 206, 250)
    LIGHT_SLATE_GRAY        = Color.of(119, 136, 153)
    LIGHT_STEEL_BLUE        = Color.of(176, 196, 222)
    LIGHT_YELLOW            = Color.of(255, 255, 224)
    LIME_GREEN              = Color.of(50, 205, 50)
    LINEN                   = Color.of(250, 240, 230)
    MAGENTA                 = Color.of(255, 0, 255)
    MAROON                  = Color.of(128, 0, 0)
    MEDIUM_AQUA_MARINE      = Color.of(102, 205, 170)
    MEDIUM_BLUE             = Color.of(0, 0, 205)
    MEDIUM_ORCHID           = Color.of(186, 85, 211)
    MEDIUM_PURPLE           = Color.of(147, 112, 219)
    MEDIUM_SEA_GREEN        = Color.of(60, 179, 113)
    MEDIUM_SLATE_BLUE       = Color.of(123, 104, 238)
    MEDIUM_SPRING_GREEN     = Color.of(0, 250, 154)
    MEDIUM_TURQUOISE        = Color.of(72, 209, 204)
    MEDIUM_VIOLET_RED       = Color.of(199, 21, 133)
    MIDNIGHT_BLUE           = Color.of(25, 25, 112)
    MINT_CREAM              = Color.of(245, 255, 250)
    MISTY_ROSE              = Color.of(255, 228, 225)
    MOCCASIN                = Color.of(255, 228, 181)
    NAVAJO_WHITE            = Color.of(255, 222, 173)
    OLD_LACE                = Color.of(253, 245, 230)
    OLIVE_DRAB              = Color.of(107, 142, 35)
    ORANGE                  = Color.of(255, 165, 0)
    ORANGE_RED              = Color.of(255, 69, 0)
    ORCHID                  = Color.of(218, 112, 214)
    PALE_GOLDEN_ROD         = Color.of(238, 232, 170)
    PALE_GREEN              = Color.of(152, 251, 152)
    PALE_TURQUOISE          = Color.of(175, 238, 238)
    PALE_VIOLET_RED         = Color.of(219, 112, 147)
    PAPAYA_WHIP             = Color.of(255, 239, 213)
    PEACH_PUFF              = Color.of(255, 218, 185)
    PERU                    = Color.of(205, 133, 63)
    PINK                    = Color.of(255, 192, 203)
    PLUM                    = Color.of(221, 160, 221)
    POWDER_BLUE             = Color.of(176, 224, 230)
    REBECCA_PURPLE          = Color.of(102, 51, 153)
    ROSY_BROWN              = Color.of(188, 143, 143)
    ROYAL_BLUE              = Color.of(65, 105, 225)
    SADDLE_BROWN            = Color.of(139, 69, 19)
    SALMON                  = Color.of(250, 128, 114)
    SANDY_BROWN             = Color.of(244, 164, 96)
    SEA_GREEN               = Color.of(46, 139, 87)
    SEA_SHELL               = Color.of(255, 245, 238)
    SIENNA                  = Color.of(160, 82, 45)
    SKY_BLUE                = Color.of(135, 206, 235)
    SLATE_BLUE              = Color.of(106, 90, 205)
    SLATE_GRAY              = Color.of(112, 128, 144)
    SNOW                    = Color.of(255, 250, 250)
    SPRING_GREEN            = Color.of(0, 255, 127)
    STEEL_BLUE              = Color.of(70, 130, 180)
    TAN                     = Color.of(210, 180, 140)
    THISTLE                 = Color.of(216, 191, 216)
    TOMATO                  = Color.of(255, 99, 71)
    TURQUOISE               = Color.of(64, 224, 208)
    VIOLET                  = Color.of(238, 130, 238)
    WHEAT                   = Color.of(245, 222, 179)
    WHITE_SMOKE             = Color.of(245, 245, 245)
    YELLOW_GREEN            = Color.of(154, 205, 50)
    # yapf: enable

    @classmethod
    def blend(cls, color1: Color, color2: Color, t: float) -> Color:
        """Linearly interpolate between two colors.

        color = (1 - t) * color1 + t * color2
        """
        return Color.of(
            round((1 - t) * color1.r + t * color2.r),
            round((1 - t) * color1.g + t * color2.g),
            round((1 - t) * color1.b + t * color2.b),
            round((1 - t) * color1.a + t * color2.a),
        )

    @classmethod
    def natural_blend(cls, color1: Color, color2: Color, t: float) -> Color:
        """Natural color mixing by Mixbox (https://github.com/scrtwpns/mixbox)."""
        if lerp is None:
            return cls.blend(color1, color2, t)
        color = lerp(color1, color2, t)
        return Color.of(*color)

    @classmethod
    def named_colors(cls) -> Generator[tuple[str, Color], None, None]:
        for name, color in cls.__dict__.items():
            if isinstance(color, Color):
                yield name, color

    @classmethod
    def colors(cls) -> Generator[Color, None, None]:
        for _, color in cls.named_colors():
            if isinstance(color, Color):
                yield color
