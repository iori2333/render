from abc import ABC, abstractmethod
from typing import Iterable
from typing_extensions import TypedDict

from .cacheable import Cacheable
from .color import Color, Palette
from .decorations import Decoration, Decorations
from .image import RenderImage
from .properties import Border, Space


class BaseStyle(TypedDict, total=False):
    """Base style of a render object.

    Args:
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
    decorations: Iterable[Decoration]


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
        decorations: Iterable[Decoration] = (),
        background: Color = Palette.TRANSPARENT,
    ) -> None:
        Cacheable.__init__(self)
        self.border = border
        self.margin = margin
        self.padding = padding
        self.decorations = Decorations.of(*decorations)
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
        """Width of the object.

        Note:
            This method should NOT be @cached.
            Add @cached to `content_width`.
        """
        width = self.content_width + self.padding.width + self.margin.width + self.border.width * 2
        return width

    @property
    def height(self) -> int:
        """Height of the object.

        Note:
            This method should NOT be @cached.
            Add @cached to `content_height`.
        """
        height = self.content_height + self.padding.height + self.margin.height + self.border.width * 2
        return height

    def render(self) -> RenderImage:
        """Render an object to image.

        Render process:
            1. Render content (implemented by subclasses)
            2. Apply content decorations
            3. Draw border & fill background
            4. Apply full decorations
            5. Apply background decorations if needed

        Note:
            This method should NOT be @cached.
            Add @cached to `render_content`.
        """

        im = RenderImage.empty(self.width, self.height, Palette.TRANSPARENT)
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
        if self.decorations.has_bg_decorations:
            bg = RenderImage.empty(
                self.width,
                self.height,
                color=Palette.TRANSPARENT,
            )
            bg = self.decorations.apply_background(im, bg, self)
            im = bg.paste(0, 0, im)
        return im
