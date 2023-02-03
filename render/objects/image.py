from __future__ import annotations

from contextlib import contextmanager
from typing import Generator
from typing_extensions import Self, Unpack, override

from render.base import BaseStyle, Color, RenderImage, RenderObject, volatile
from render.utils import PathLike


class Image(RenderObject):
    """A RenderObject wrapping a RenderImage.

    Attributes:
        im: The wrapped RenderImage.

    Note:
        The wrapped RenderImage is set to be read-only to prevent
        accidental modification.
        If modification is necessary, use the modify context manager
        to ensure the cache is cleared.
    """

    def __init__(self, im: RenderImage, **kwargs: Unpack[BaseStyle]) -> None:
        super().__init__(**kwargs)
        with volatile(self):
            self.im = im
            self.im.base_im.setflags(write=False)

    @contextmanager
    def modify(self) -> Generator[None, None, None]:
        """Context manager that temporarily sets the wrapped RenderImage to be
        writable.
        """
        self.im.base_im.setflags(write=True)
        yield
        self.clear_cache()
        self.im.base_im.setflags(write=False)

    @classmethod
    def from_file(
        cls,
        path: PathLike,
        resize: float | tuple[int, int] | None = None,
        **kwargs: Unpack[BaseStyle],
    ) -> Self:
        im = RenderImage.from_file(path)
        if resize is not None:
            if isinstance(resize, tuple):
                im = im.resize(*resize)
            else:
                im = im.resize(int(im.width * resize), int(im.height * resize))
        return Image(im, **kwargs)

    @classmethod
    def from_image(cls, im: RenderImage, **kwargs: Unpack[BaseStyle]) -> Self:
        """Create a new Image from an existing RenderImage.

        Note:
            Copy is used to cut off the reference to the original RenderImage.
        """
        return Image(im.copy(), **kwargs)

    @classmethod
    def from_color(cls, width: int, height: int, color: Color,
                   **kwargs: Unpack[BaseStyle]) -> Self:
        return Image(RenderImage.empty(width, height, color), **kwargs)

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
