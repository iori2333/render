from enum import Enum
from typing import Iterable, Tuple
from typing_extensions import override, Self, Unpack

from render.base import RenderObject, RenderImage, Alignment, Direction, BaseStyle


class Container(RenderObject):

    def __init__(
        self,
        alignment: Alignment,
        direction: Direction,
        children: Iterable[RenderObject],
        **kwargs: Unpack[BaseStyle],
    ) -> None:
        super(Container, self).__init__(**kwargs)
        self.alignment = alignment
        self.direction = direction
        self.children = list(children)

    @classmethod
    def from_children(
        cls,
        children: Iterable[RenderObject],
        alignment: Alignment = Alignment.START,
        direction: Direction = Direction.HORIZONTAL,
        **kwargs: Unpack[BaseStyle],
    ) -> Self:
        return cls(alignment, direction, children, **kwargs)

    @property
    @override
    def content_width(self) -> int:
        if self.direction == Direction.HORIZONTAL:
            return sum(child.width for child in self.children)
        else:
            return max(child.width
                       for child in self.children) if self.children else 0

    @property
    @override
    def content_height(self) -> int:
        if self.direction == Direction.HORIZONTAL:
            return max(child.height
                       for child in self.children) if self.children else 0
        else:
            return sum(child.height for child in self.children)

    @override
    def render_content(self) -> RenderImage:
        if not self.children:
            return RenderImage.empty(0, 0)
        rendered = map(lambda child: child.render(), self.children)
        concat = RenderImage.concat(rendered, self.direction, self.alignment,
                                    self.background)
        return concat


class JustifyContent(Enum):
    SPACE_BETWEEN = 1
    SPACE_AROUND = 2
    SPACE_EVENLY = 3
    START = 4
    END = 5
    CENTER = 6


class FixedContainer(Container):

    def __init__(
        self,
        width: int,
        height: int,
        justify_content: JustifyContent,
        alignment: Alignment,
        direction: Direction,
        children: Iterable[RenderObject],
        **kwargs: Unpack[BaseStyle],
    ) -> None:
        super(FixedContainer, self).__init__(alignment, direction, children,
                                             **kwargs)
        self._width = width
        self._height = height
        self.justifyContent = justify_content

    @property
    @override
    def content_width(self) -> int:
        return self._width

    @property
    @override
    def content_height(self) -> int:
        return self._height

    @classmethod
    def from_children(
        cls,
        width: int,
        height: int,
        children: Iterable[RenderObject],
        justify_content: JustifyContent = JustifyContent.START,
        alignment: Alignment = Alignment.START,
        direction: Direction = Direction.HORIZONTAL,
        **kwargs: Unpack[BaseStyle],
    ) -> Self:
        if direction == Direction.HORIZONTAL:
            min_width = sum(child.width for child in children)
            min_height = max(child.height
                             for child in children) if children else 0
        else:
            min_width = max(child.width
                            for child in children) if children else 0
            min_height = sum(child.height for child in children)

        if width < min_width or height < min_height:
            raise ValueError("Container is too small")

        return cls(width, height, justify_content, alignment, direction,
                   children, **kwargs)

    def _render_boundary(self) -> Tuple[int, int]:
        if self.direction == Direction.HORIZONTAL:
            space = self.content_width - sum(child.width
                                             for child in self.children)
        else:
            space = self.content_height - sum(child.height
                                              for child in self.children)

        if self.justifyContent == JustifyContent.SPACE_BETWEEN:
            n = len(self.children) - 1
            space = space // n if n > 0 else 0
            offset = 0
        elif self.justifyContent == JustifyContent.SPACE_AROUND:
            space = space // len(self.children)
            offset = space // 2
        elif self.justifyContent == JustifyContent.SPACE_EVENLY:
            space = space // (len(self.children) + 1)
            offset = space
        elif self.justifyContent == JustifyContent.CENTER:
            space = 0
            offset = (self.width - sum(child.width
                                       for child in self.children)) // 2
        elif self.justifyContent == JustifyContent.END:
            space = 0
            offset = self.width - sum(child.width for child in self.children)
        else:
            space = 0
            offset = 0

        return space, offset

    @override
    def render_content(self) -> RenderImage:
        rendered = list(map(lambda child: child.render(), self.children))
        concat = RenderImage.empty(self.content_width, self.content_height,
                                   self.background)

        space, offset = self._render_boundary()
        for child in rendered:
            if self.direction == Direction.HORIZONTAL:
                if self.alignment == Alignment.START:
                    y = 0
                elif self.alignment == Alignment.CENTER:
                    y = (self.content_height - child.height) // 2
                else:
                    y = self.content_height - child.height
                concat = concat.paste(offset, y, child)
                offset += child.width + space
            else:
                if self.alignment == Alignment.START:
                    x = 0
                elif self.alignment == Alignment.CENTER:
                    x = (self.content_width - child.width) // 2
                else:
                    x = self.content_width - child.width
                concat = concat.paste(x, offset, child)
                offset += child.height + space
        return concat
