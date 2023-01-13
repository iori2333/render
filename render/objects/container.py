from typing import Iterable, Self
from typing_extensions import override

from render.base import RenderObject, RenderImage, Alignment, Direction, Color
from ..base.color import Palette


class Container(RenderObject):

    def __init__(
        self,
        alignment: Alignment,
        direction: Direction,
        background: Color,
        children: Iterable[RenderObject],
        **kwargs,
    ) -> None:
        super(Container, self).__init__(**kwargs)
        self.alignment = alignment
        self.direction = direction
        self.children = list(children)
        self.background = background

    @classmethod
    def from_children(
        cls,
        children: Iterable[RenderObject],
        alignment: Alignment = Alignment.START,
        direction: Direction = Direction.HORIZONTAL,
        **kwargs,
    ) -> Self:
        return cls(alignment, direction, Palette.TRANSPARENT, children, **kwargs)

    @property
    @override
    def content_width(self) -> int:
        if self.direction == Direction.HORIZONTAL:
            return sum(child.width for child in self.children)
        else:
            return max(child.width for child in self.children)

    @property
    @override
    def content_height(self) -> int:
        if self.direction == Direction.HORIZONTAL:
            return max(child.height for child in self.children)
        else:
            return sum(child.height for child in self.children)

    @override
    def render_content(self) -> RenderImage:
        rendered = map(lambda child: child.render(), self.children)
        concat = RenderImage.concat(rendered, self.direction, self.alignment)
        return concat
