from typing_extensions import Self, override

from render.base import RenderObject, RenderImage, Palette


class Spacer(RenderObject):
    """A spacer for holding space in containers."""

    def __init__(self, width: int, height: int) -> None:
        super(Spacer, self).__init__()
        self.im = RenderImage.empty(width, height, color=Palette.TRANSPARENT)

    @classmethod
    def of(cls, width: int = 0, height: int = 0) -> Self:
        return Spacer(width, height)

    @property
    @override
    def content_width(self) -> int:
        return self.im.width

    @property
    @override
    def content_height(self) -> int:
        return self.im.height

    @override
    def render_content(self) -> RenderImage:
        return self.im
