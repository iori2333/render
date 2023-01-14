from abc import ABC, abstractmethod
from typing import Optional

from .color import Color, Palette
from .image import RenderImage
from .properties import Space, Border


class RenderObject(ABC):

    def __init__(
        self,
        background: Color = Palette.TRANSPARENT,
        border: Optional[Border] = None,
        margin: Space = Space.zero(),
        padding: Space = Space.zero(),
    ) -> None:
        self.background = background
        self.border = border
        self.margin = margin
        self.padding = padding

    @property
    @abstractmethod
    def content_width(self) -> int:
        raise NotImplementedError()

    @property
    @abstractmethod
    def content_height(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def render_content(self) -> RenderImage:
        raise NotImplementedError()

    @property
    def width(self) -> int:
        width = self.content_width + self.padding.left + self.padding.right
        if self.border is not None:
            width += self.border.width * 2
        return width + self.margin.left + self.margin.right

    @property
    def height(self) -> int:
        height = self.content_height + self.padding.top + self.padding.bottom
        if self.border is not None:
            height += self.border.width * 2
        return height + self.margin.top + self.margin.bottom

    def render(self) -> RenderImage:
        im = RenderImage.empty(self.width, self.height, self.background)
        content = self.render_content()
        border_width = self.border.width if self.border is not None else 0
        if self.border is not None:
            im = im.draw_border(
                self.margin.left + border_width,
                self.margin.top + border_width,
                self.content_width + self.padding.left + self.padding.right,
                self.content_height + self.padding.top + self.padding.bottom,
                self.border,
            )
        return im.paste(
            content,
            self.margin.left + border_width + self.padding.left,
            self.margin.top + border_width + self.padding.top,
        )
