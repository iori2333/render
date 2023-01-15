from typing import Union, Optional, Tuple
from typing_extensions import override, Self, Unpack

from render.base import RenderObject, RenderImage, BaseStyle


class Image(RenderObject):

    def __init__(self, im: RenderImage, **kwargs: Unpack[BaseStyle]) -> None:
        super(Image, self).__init__(**kwargs)
        self.im = im

    @classmethod
    def from_file(
        cls,
        path: str,
        resize: Optional[Union[float, Tuple[int, int]]] = None,
        **kwargs: Unpack[BaseStyle],
    ) -> Self:
        im = RenderImage.from_file(path)
        if resize is not None:
            if isinstance(resize, tuple):
                im = im.resize(*resize)
            else:
                im = im.resize(int(im.width * resize), int(im.height * resize))
        return cls.from_image(im, **kwargs)

    @classmethod
    def from_image(cls, im: RenderImage, **kwargs: Unpack[BaseStyle]) -> Self:
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
