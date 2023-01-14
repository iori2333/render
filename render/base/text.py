from typing import Optional
from typing_extensions import Self

import numpy as np
from PIL import ImageFont, ImageDraw, Image, features

from .color import Color, Palette
from .image import RenderImage


class RenderText:

    def __init__(
        self,
        text: str,
        font: str,
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
        font: str,
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
        font = ImageFont.truetype(self.font, self.size)
        width, height = font.getsize(self.text)
        im = Image.new("RGBA", (width, height), self.background.as_tuple())
        draw = ImageDraw.Draw(im)
        draw.text(
            (0, 0),
            self.text,
            self.color.as_tuple(),
            font=font,
            anchor="lt",
            features=["-kern"] if features.check("raqm") else None,
        )
        return RenderImage.from_raw(np.asarray(im))
