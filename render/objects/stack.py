from typing import Iterable, Optional
from typing_extensions import override, Self

from render.base import RenderObject, RenderImage, Alignment


class Stack(RenderObject):

    def __init__(
        self,
        children: Iterable[RenderObject],
        vertical_alignment: Alignment,
        horizontal_alignment: Alignment,
        **kwargs,
    ) -> None:
        super(Stack, self).__init__(**kwargs)
        self.children = list(children)
        self.vertical_alignment = vertical_alignment
        self.horizontal_alignment = horizontal_alignment

    @classmethod
    def from_children(
        cls,
        children: Iterable[RenderObject],  # bottom to top
        alignment: Alignment = Alignment.START,
        vertical_alignment: Optional[Alignment] = None,
        horizontal_alignment: Optional[Alignment] = None,
        **kwargs,
    ) -> Self:
        if vertical_alignment is None:
            vertical_alignment = alignment
        if horizontal_alignment is None:
            horizontal_alignment = alignment
        return cls(children, vertical_alignment, horizontal_alignment,
                   **kwargs)

    @property
    @override
    def content_width(self) -> int:
        return max(child.width for child in self.children)

    @property
    @override
    def content_height(self) -> int:
        return max(child.height for child in self.children)

    @override
    def render_content(self) -> RenderImage:
        rendered = map(lambda child: child.render(), self.children)
        im = RenderImage.empty(self.width, self.height, self.background)
        for child in rendered:
            if self.vertical_alignment == Alignment.START:
                y = 0
            elif self.vertical_alignment == Alignment.CENTER:
                y = (self.height - child.height) // 2
            else:
                y = self.height - child.height

            if self.horizontal_alignment == Alignment.START:
                x = 0
            elif self.horizontal_alignment == Alignment.CENTER:
                x = (self.width - child.width) // 2
            else:
                x = self.width - child.width

            im = im.paste(child, x, y)
        return im
