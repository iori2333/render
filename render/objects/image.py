from typing_extensions import override, Self

from render.base import RenderObject, RenderImage


class Image(RenderObject):

    def __init__(self, im: RenderImage, **kwargs) -> None:
        super(Image, self).__init__(**kwargs)
        self.im = im

    @classmethod
    def from_file(cls, path: str, **kwargs) -> Self:
        im = RenderImage.from_file(path)
        assert im is not None, f"Failed to load image from {path}"
        return cls.from_image(im, **kwargs)

    @classmethod
    def from_image(cls, im: RenderImage, **kwargs) -> Self:
        return Image(im, **kwargs)

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
