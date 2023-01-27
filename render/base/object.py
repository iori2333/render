from abc import ABC, abstractmethod
from typing import Iterable
from typing_extensions import TypedDict

from .cacheable import Cacheable
from .decorations import Decoration, Decorations
from .color import Color, Palette
from .image import RenderImage
from .properties import Space, Border


class BaseStyle(TypedDict, total=False):
    background: Color
    border: Border
    margin: Space
    padding: Space
    decorations: Iterable[Decoration]


class RenderObject(ABC, Cacheable):
    """
    Base class of all renderable objects.

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
        width = self.content_width + self.padding.width + self.margin.width + self.border.width * 2
        return width

    @property
    def height(self) -> int:
        height = self.content_height + self.padding.height + self.margin.height + self.border.width * 2
        return height

    def render(self) -> RenderImage:
        """
        Render an object to image.

        Render process:
        1. Render content (implemented by subclasses)
        2. Apply content decorations
        3. Draw border
        4. Apply full decorations
        5. Apply background decorations if needed
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
