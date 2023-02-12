from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

import cv2
import numpy as np
import PIL.Image as PILImage
from typing_extensions import TypedDict

from .cacheable import Cacheable
from .color import Color, Palette
from .decorations import Decoration, Decorations
from .image import RenderImage
from .properties import Border, BoundingBox, Space


class BaseStyle(TypedDict, total=False):
    """Base style of a render object.

    Fields:
        background: background color filled inside the border
        padding: padding (px) of the object
        border: width (px) and color of the border
        margin: margin (px) of the object
        decorations: decorations of the object

    Box model:
        margin -> border -> padding -> content

        +-------------------+
        | margin            |
        | +---------------+ |
        | | border        | |
        | | +-----------+ | |
        | | | padding   | | |
        | | | +-------+ | | |
        | | | |       | | | |
        | | | |content| | | |
        | | | |       | | | |
        | | | +-------+ | | |
        | | +-----------+ | |
        | +---------------+ |
    """
    background: Color
    margin: Space
    border: Border
    padding: Space
    decorations: Iterable[Decoration] | Decorations


class RenderObject(ABC, Cacheable):
    """Base class of all renderable objects.

    Abstract Methods:
        content_width: int - width of the object
        content_height: int - height of the object
        render_content(): RenderImage - render the object

    Content width and height must be determined before rendering.
    """

    def __init__(
        self,
        border: Border = Border.zero(),
        margin: Space = Space.zero(),
        padding: Space = Space.zero(),
        decorations: Iterable[Decoration] | Decorations = (),
        background: Color = Palette.TRANSPARENT,
    ) -> None:
        Cacheable.__init__(self)
        self.tree_nodes = []
        self.depth = 1
        self.offset_from_origin = (0, 0)
        self.border = border
        self.margin = margin
        self.padding = padding
        self.background = background
        if isinstance(decorations, Decorations):
            self.decorations = decorations
        else:
            self.decorations = Decorations.of(*decorations)

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
        """Width of the object.

        Note:
            This method should NOT be @cached.
            Add @cached to `content_width`.
        """
        width = (self.content_width + self.padding.width + self.margin.width +
                 self.border.width * 2)
        return width

    @property
    def height(self) -> int:
        """Height of the object.

        Note:
            This method should NOT be @cached.
            Add @cached to `content_height`.
        """
        height = (self.content_height + self.padding.height +
                  self.margin.height + self.border.width * 2)
        return height

    @property
    def border_box(self) -> BoundingBox:
        return BoundingBox.of(
            self.margin.left,
            self.margin.top,
            self.content_width + self.padding.width + self.border.width * 2,
            self.content_height + self.padding.height + self.border.width * 2,
        )

    @property
    def padding_box(self) -> BoundingBox:
        return BoundingBox.of(
            self.margin.left + self.border.width,
            self.margin.top + self.border.width,
            self.content_width + self.padding.width,
            self.content_height + self.padding.height,
        )

    @property
    def content_box(self) -> BoundingBox:
        return BoundingBox.of(
            self.margin.left + self.border.width + self.padding.left,
            self.margin.top + self.border.width + self.padding.top,
            self.content_width,
            self.content_height,
        )

    def render_tree_preparation(self, depth: int, offset: tuple[int, int]) -> bool:
        self.tree_nodes = []
        self.depth = depth
        self.offset_from_origin = offset
        return False
    
    def render_self(self) -> cv2.Mat:
        raise NotImplementedError()
    
    def render(self) -> RenderImage:
        """Render an object to image.

        Render / Decorate steps:
            1. Create an empty canvas   / Apply initial decorations
            2. Render content to canvas / Apply after content decorations
            3. Fill padding area        / Apply before padding to padding only
                                        / Apply after padding to canvas
            4. Draw border              / Apply final decorations

        Note:
            This method should NOT be @cached.
            Add @cached to `render_content`.
        """
        self.render_tree_preparation(1, (0, 0))
        curernt_layer, next_layer = self.tree_nodes, []
        final_image = PILImage.fromarray(self.render_self())
        depth = self.depth
        while depth > 0 and curernt_layer:
            depth = max([i.depth for i in curernt_layer])
            for item in curernt_layer:
                if item.depth != depth:
                    next_layer.append(item)
                elif item.decorations:
                    offset = item.offset_from_origin
                    final_image.alpha_composite(PILImage.fromarray(item.render().base_im), offset)
                else:
                    offset = item.offset_from_origin
                    for node in item.tree_nodes:
                        next_layer.append(node)
                    final_image.alpha_composite(PILImage.fromarray(item.render_self()), offset)
            curernt_layer, next_layer = next_layer, []
            depth -= 1
        if self.decorations:
            content_box = self.content_box
            padding_box = self.padding_box
            canvas = self.decorations.apply_initial(RenderImage.empty(self.width, self.height), self)
            canvas = canvas.paste(content_box.x, content_box.y, RenderImage(np.array(final_image)))
            canvas = self.decorations.apply_after_content(canvas, self)

            padding = RenderImage.empty(self.width, self.height).fill(
                padding_box.x,
                padding_box.y,
                padding_box.w,
                padding_box.h,
                color=self.background,
            )
            canvas = self.decorations.apply_before_padding(padding, self).paste(0, 0, canvas)
            canvas = self.decorations.apply_after_padding(canvas, self)

            canvas = canvas.draw_border(
                padding_box.x,
                padding_box.y,
                padding_box.w - 1,
                padding_box.h - 1,
                self.border,
            )
            final_image = self.decorations.apply_final(canvas, self)
        else:
            final_image = RenderImage(np.array(final_image))
        return final_image
