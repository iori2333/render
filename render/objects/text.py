from typing_extensions import override

from render.base import RenderObject, RenderImage, RenderText, Color, Palette


class Text(RenderObject):

    def __init__(
        self,
        text: str,
        font: str,
        size: int = 12,
        color: Color | None = Palette.BLACK,
        background: Color = Palette.TRANSPARENT,
        **kwargs,
    ) -> None:
        super(Text, self).__init__(**kwargs)
        self.render_text = RenderText.of(text, font, size, color, background)
        self._pre_rendered = self.render_text.render()

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
