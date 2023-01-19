from typing import Optional
from typing_extensions import Self

import numpy as np
from PIL import ImageFont, ImageDraw, Image

from render.utils import PathLike
from .color import Color, Palette
from .image import RenderImage


class RenderText:

    def __init__(
        self,
        text: str,
        font: PathLike,
        size: int,
        color: Color = Palette.BLACK,
        background: Color = Palette.TRANSPARENT,
    ):
        self.text = text
        self.font = font
        self.size = size
        self.color = color
        self.background = background

    @classmethod
    def of(
        cls,
        text: str,
        font: PathLike,
        size: int = 12,
        color: Optional[Color] = None,
        background: Color = Palette.TRANSPARENT,
    ) -> Self:
        if color is None:
            r, g, b = background.to_rgb()
            lightness = 0.2126 * r + 0.7152 * g + 0.0722 * b
            color = Palette.WHITE if lightness < 128 else Palette.BLACK
        return cls(text, font, size, color, background)

    def render(self) -> RenderImage:
        font = ImageFont.truetype(str(self.font), self.size)
        width, _ = font.getsize(self.text)
        ascent, descent = font.getmetrics()
        # height always equals to max possible height of the font
        # instead of actual height of the text for better alignment
        height = ascent + descent
        im = Image.new("RGBA", (width, height), self.background)
        draw = ImageDraw.Draw(im)
        draw.text(
            (0, 0),
            self.text,
            self.color,
            font=font,
        )
        return RenderImage.from_raw(np.asarray(im))

    @property
    def baseline(self) -> int:
        """Distance from the top to the baseline of the text."""
        font = ImageFont.truetype(str(self.font), self.size)
        ascent, _ = font.getmetrics()
        return ascent

    @property
    def width(self) -> int:
        font = ImageFont.truetype(str(self.font), self.size)
        width, _ = font.getsize(self.text)
        return width
