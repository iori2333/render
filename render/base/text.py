from __future__ import annotations

from enum import Flag, auto
from typing_extensions import Self

from PIL import Image, ImageDraw, ImageFont

from render.utils import PathLike
from .cacheable import Cacheable, cached, volatile
from .color import Color, Palette
from .image import RenderImage


class TextDecoration(Flag):
    NONE = 0
    UNDERLINE = auto()
    OVERLINE = auto()
    LINE_THROUGH = auto()


class RenderText(Cacheable):
    """Render text to an image in one single line.

    Attributes:
        text: text to render.
        font: font file path.
        size: font size.
        color: text color.
        stroke_width: width of stroke.
        stroke_color: color of stroke.
        decoration: text decoration. See `TextDecoration`.
        decoration_thickness: thickness of text decoration lines.
    """

    def __init__(
        self,
        text: str,
        font: PathLike,
        size: int,
        color: Color = Palette.BLACK,
        stroke_width: int = 0,
        stroke_color: Color | None = None,
        decoration: TextDecoration = TextDecoration.NONE,
        decoration_thickness: int = -1,
    ):
        super().__init__()
        with volatile(self):
            self.text = text
            self.font = font
            self.size = size
            self.color = color
            self.stroke_width = stroke_width
            self.stroke_color = stroke_color
            self.decoration = decoration
            self.decoration_thickness = decoration_thickness

    @classmethod
    def of(
        cls,
        text: str,
        font: PathLike,
        size: int = 12,
        color: Color | None = None,
        stroke_width: int = 0,
        stroke_color: Color | None = None,
        decoration: TextDecoration = TextDecoration.NONE,
        decoration_thickness: int = -1,
        background: Color = Palette.TRANSPARENT,
    ) -> Self:
        """Create a `RenderText` instance with default values.

        If `color` is not specified, it will be automatically chosen
        from BLACK or WHITE based on the background color luminance.
        """
        if color is None:
            r, g, b = background.to_rgb()
            luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
            color = Palette.WHITE if luminance < 128 else Palette.BLACK
        if decoration_thickness < 0:
            decoration_thickness = max(size // 10, 1)
        return cls(text, font, size, color, stroke_width, stroke_color,
                   decoration, decoration_thickness)

    @cached
    def render(self) -> RenderImage:
        font = ImageFont.truetype(str(self.font), self.size)
        # 1. calculate font metrics and text bounding box
        l, t, r, _ = font.getbbox(self.text,
                                  mode="RGBA",
                                  stroke_width=self.stroke_width,
                                  anchor="ls")
        ascent, descent = font.getmetrics()
        width = r - l
        height = ascent + descent + self.stroke_width * 2
        # 2. draw text
        im = Image.new("RGBA", (width, height), color=Palette.TRANSPARENT)
        draw = ImageDraw.Draw(im)
        draw.text(
            xy=(self.stroke_width, self.stroke_width),
            text=self.text,
            fill=self.color,
            font=font,
            stroke_width=self.stroke_width,
            stroke_fill=self.stroke_color,
        )
        # 3. draw decoration
        lines_y = []
        thick = self.decoration_thickness
        half_thick = thick // 2 + 1
        if self.decoration & TextDecoration.UNDERLINE:
            lines_y.append(self.baseline + half_thick)
        if self.decoration & TextDecoration.OVERLINE:
            lines_y.append(ascent + t - half_thick)  # t < 0
        if self.decoration & TextDecoration.LINE_THROUGH:
            # deco_y.append((ascent + t + self.baseline) // 2 + half_thick)
            lines_y.append(height // 2 + half_thick)
        for y in lines_y:
            draw.line(
                xy=[(0, y), (width, y)],
                fill=self.color,
                width=thick,
            )
        return RenderImage.from_pil(im)

    @property
    @cached
    def baseline(self) -> int:
        """Distance from the top to the baseline of the text."""
        font = ImageFont.truetype(str(self.font), self.size)
        ascent, _ = font.getmetrics()
        return ascent + self.stroke_width

    @property
    @cached
    def width(self) -> int:
        font = ImageFont.truetype(str(self.font), self.size)
        width, _ = font.getsize(self.text, stroke_width=self.stroke_width)
        return width

    @property
    @cached
    def height(self) -> int:
        font = ImageFont.truetype(str(self.font), self.size)
        ascent, descent = font.getmetrics()
        return ascent + descent + self.stroke_width * 2
