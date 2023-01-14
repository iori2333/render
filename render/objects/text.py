from typing import Optional
from typing_extensions import override, Self

from render.base import RenderObject, RenderImage, RenderText, Color, Palette


class Text(RenderObject):

    def __init__(
        self,
        render_text: RenderText,
        **kwargs,
    ) -> None:
        super(Text, self).__init__(background=render_text.background, **kwargs)
        self.render_text = render_text
        self._pre_rendered = render_text.render()

    @classmethod
    def of(
        cls,
        text: str,
        font: str,
        size: int = 12,
        color: Optional[Color] = None,
        background: Color = Palette.TRANSPARENT,
        **kwargs,
    ) -> Self:
        render_text = RenderText.of(text, font, size, color, background)
        return cls(render_text, **kwargs)

    @classmethod
    def from_text(
        cls,
        render_text: RenderText,
        **kwargs,
    ) -> Self:
        return cls(render_text, **kwargs)

    @property
    @override
    def content_width(self) -> int:
        return self._pre_rendered.width

    @property
    @override
    def content_height(self) -> int:
        return self._pre_rendered.height

    @override
    def render_content(self) -> RenderImage:
        return self._pre_rendered
