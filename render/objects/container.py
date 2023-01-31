from __future__ import annotations

from enum import Enum
from typing import Iterable
from typing_extensions import Self, Unpack, override

from render.base import (Alignment, BaseStyle, Direction, RenderImage,
                         RenderObject, cached, volatile)


class Container(RenderObject):
    """A container that arranges its children linearly.

    Attributes:
        children: list of children to be arranged.
        alignment: alignment of children. start, end or center.
        direction: direction of arrangement. horizontal or vertical.
    """

    def __init__(
        self,
        alignment: Alignment,
        direction: Direction,
        children: Iterable[RenderObject],
        **kwargs: Unpack[BaseStyle],
    ) -> None:
        super().__init__(**kwargs)
        with volatile(self) as vlt:
            self.alignment = alignment
            self.direction = direction
            self.children = vlt.list(children)

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
    @cached
    @override
    def content_width(self) -> int:
        if self.direction == Direction.HORIZONTAL:
            return sum(child.width for child in self.children)
        return max(child.width
                   for child in self.children) if self.children else 0

    @property
    @cached
    @override
    def content_height(self) -> int:
        if self.direction == Direction.HORIZONTAL:
            return max(child.height
                       for child in self.children) if self.children else 0
        return sum(child.height for child in self.children)

    @cached
    @override
    def render_content(self) -> RenderImage:
        if not self.children:
            return RenderImage.empty(0, 0)
        rendered = map(lambda child: child.render(), self.children)
        concat = RenderImage.concat(rendered, self.direction, self.alignment)
        return concat


class JustifyContent(Enum):
    """How to justify children in a container."""

    # Evenly distribute, first flush with start, last flush with end.
    SPACE_BETWEEN = 1
    # Evenly distribute, either end has half the space.
    SPACE_AROUND = 2
    # Evenly distribute, equal space for all.
    SPACE_EVENLY = 3
    # Flush with start, possibly with space at end.
    START = 4
    # Flush with end, possibly with space at start.
    END = 5
    # Center, possibly with space at both ends.
    CENTER = 6


class FixedContainer(Container):
    """A container like Container, but with fixed width and height.

    Attributes:
        _width: fixed content width.
        _height: fixed content height.
        justifyContent: how to justify children.
    """
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
        super().__init__(alignment, direction, children, **kwargs)
        with volatile(self):
            self.fixed_width = width
            self.fixed_height = height
            self.justifyContent = justify_content

    @property
    @override
    def content_width(self) -> int:
        return self.fixed_width

    @property
    @override
    def content_height(self) -> int:
        return self.fixed_height

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
            raise ValueError(f"Container is too small, "
                             f"expect at least {(min_width, min_height)}, "
                             f"got {(width, height)}")

        return cls(width, height, justify_content, alignment, direction,
                   children, **kwargs)

    @cached
    def _render_boundary(self) -> tuple[int, int]:
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

    @cached
    @override
    def render_content(self) -> RenderImage:
        rendered = list(map(lambda child: child.render(), self.children))
        concat = RenderImage.empty(self.content_width, self.content_height)

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
