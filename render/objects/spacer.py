from typing_extensions import Self, override

from render.base import RenderObject, RenderImage, Palette, volatile, cached


class Spacer(RenderObject):
    """A spacer for holding space in containers."""

    def __init__(self, width: int, height: int) -> None:
        super(Spacer, self).__init__()
        with volatile(self):
            self.space_width = width
            self.space_height = height

    @classmethod
    def of(cls, width: int = 0, height: int = 0) -> Self:
        return Spacer(width, height)

    @property
    @override
    def content_width(self) -> int:
        return self.space_width

    @property
    @override
    def content_height(self) -> int:
        return self.space_height

    @cached
    @override
    def render_content(self) -> RenderImage:
        return RenderImage.empty(self.space_width, self.space_height)
