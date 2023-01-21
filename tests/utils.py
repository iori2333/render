from typing import Optional
from typing_extensions import Self, Unpack, override

from render import *


class TestRect(RenderObject):

    def __init__(self, width, height, **kwargs: Unpack[BaseStyle]):
        super().__init__(**kwargs)
        self.rect_width = width
        self.rect_height = height

    @classmethod
    def of(cls, width: int, height: int, color: Optional[Color]) -> Self:
        return cls(width, height, background=color or Color.rand())

    @property
    @override
    def content_height(self) -> int:
        return self.rect_height

    @property
    @override
    def content_width(self) -> int:
        return self.rect_width

    @override
    def render_content(self) -> RenderImage:
        return RenderImage.empty(self.rect_width, self.rect_height)


__all__ = ['TestRect']
