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
        stroke_width: int = 0,
        stroke_color: Optional[Color] = None,
        background: Color = Palette.TRANSPARENT,
    ):
        self.text = text
        self.font = font
        self.size = size
        self.color = color
        self.stroke_width = stroke_width
        self.stroke_color = stroke_color
        self.background = background

    @classmethod
    def of(
        cls,
        text: str,
        font: PathLike,
        size: int = 12,
        color: Optional[Color] = None,
        stroke_width: int = 0,
        stroke_color: Optional[Color] = None,
        background: Color = Palette.TRANSPARENT,
    ) -> Self:
        if color is None:
            r, g, b = background.to_rgb()
            lightness = 0.2126 * r + 0.7152 * g + 0.0722 * b
            color = Palette.WHITE if lightness < 128 else Palette.BLACK
        return cls(text, font, size, color, stroke_width, stroke_color,
                   background)

    def render(self) -> RenderImage:
        font = ImageFont.truetype(str(self.font), self.size)
        width, _ = font.getsize(self.text, stroke_width=self.stroke_width)
        ascent, descent = font.getmetrics()
        # height always equals to max possible height of the font
        # instead of actual height of the text for better alignment
        height = ascent + descent + self.stroke_width * 2
        im = Image.new("RGBA", (width, height), self.background)
        draw = ImageDraw.Draw(im)
        draw.text(
            xy=(self.stroke_width, self.stroke_width),
            text=self.text,
            fill=self.color,
            font=font,
            stroke_width=self.stroke_width,
            stroke_fill=self.stroke_color,
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
        width, _ = font.getsize(self.text, stroke_width=self.stroke_width)
        return width

    @property
    def height(self) -> int:
        font = ImageFont.truetype(str(self.font), self.size)
        ascent, descent = font.getmetrics()
        return ascent + descent + self.stroke_width * 2
