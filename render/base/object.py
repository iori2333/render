from abc import ABC, abstractmethod
from typing import Optional
from typing_extensions import TypedDict

from .decorations import Decorations
from .color import Color, Palette
from .image import RenderImage
from .properties import Space, Border


class BaseStyle(TypedDict, total=False):
    background: Color
    border: Border
    margin: Space
    padding: Space


class RenderObject(ABC):

    def __init__(
        self,
        border: Border = Border.zero(),
        margin: Space = Space.zero(),
        padding: Space = Space.zero(),
        decorations: Decorations = Decorations.of(),
        background: Color = Palette.TRANSPARENT,
    ) -> None:
        self.border = border
        self.margin = margin
        self.padding = padding
        self.decorations = decorations
        self.background = background

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
        content = self.decorations.apply_content(content)

        content_width = self.content_width + self.padding.width
        content_height = self.content_height + self.padding.height
        offset_x = self.margin.left + self.border.width
        offset_y = self.margin.top + self.border.width
        im = im.draw_border(
            offset_x,
            offset_y,
            content_width - 1,
            content_height - 1,
            self.border,
        ).fill(
            offset_x,
            offset_y,
            content_width,
            content_height,
            self.background,
        ).paste(
            offset_x + self.padding.left,
            offset_y + self.padding.top,
            content,
        )

        im = self.decorations.apply_full(im)
        return im
