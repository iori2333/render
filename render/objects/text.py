import bisect
from functools import lru_cache
from typing import Callable, Generic, Optional, Sequence, TypeVar
from typing_extensions import override, Self, Unpack, Protocol

from PIL.ImageFont import FreeTypeFont, truetype

from render.base import (RenderObject, RenderImage, RenderText, Color,
                         BaseStyle, Alignment, Direction)


class Comparable(Protocol):
    def __lt__(self, other: Self) -> bool:
        ...

    def __gt__(self, other: Self) -> bool:
        ...

    def __le__(self, other: Self) -> bool:
        ...

    def __ge__(self, other: Self) -> bool:
        ...


T = TypeVar('T')
V = TypeVar('V', Comparable, int, float, str)


class BisectKeyWrapper(Generic[T, V]):
    """A wrapper class that allows to use a key function with bisect.
    
    Python 3.10 introduced the `key` parameter."""

    def __init__(self, obj: V, key: Callable[[T], V]) -> None:
        self.obj = obj
        self.key = key

    def __lt__(self, other: T) -> bool:
        return self.obj < self.key(other)

    def __gt__(self, other: T) -> bool:
        return self.obj > self.key(other)

    def __le__(self, other: T) -> bool:
        return self.obj <= self.key(other)

    def __ge__(self, other: T) -> bool:
        return self.obj >= self.key(other)


class Text(RenderObject):

    MARKS = set("；：。，！？、.,!?”》;:")

    def __init__(
        self,
        text: str,
        font: str,
        size: int,
        max_width: Optional[int],
        alignment: Alignment,
        color: Optional[Color],
        **kwargs: Unpack[BaseStyle],
    ) -> None:
        super(Text, self).__init__(**kwargs)

        self.font = font
        self.size = size
        self.alignment = alignment
        self.color = color
        self.pre_rendered = [
            RenderText.of(line, font, size, color).render()
            for line in self.cut(text, max_width)
        ]

    @staticmethod
    @lru_cache()
    def _calculate_width(font: FreeTypeFont, text: str):
        w, _ = font.getsize(text)
        return w

    @classmethod
    def _split_line(
        cls,
        font: FreeTypeFont,
        text: str,
        max_width: int,
    ) -> Sequence[str]:
        indices = list(range(len(text)))
        bound = bisect.bisect_right(
            indices,
            BisectKeyWrapper(
                max_width, key=lambda k: cls._calculate_width(font, text[:k])))
        if bound == 0:
            raise ValueError("Text is too long to fit in the given width")
        if bound == len(text):
            return [text]
        if text[bound] in cls.MARKS:
            bound -= 1
        return [text[:bound], *cls._split_line(font, text[bound:], max_width)]

    def cut(self, text: str, max_width: Optional[int]) -> Sequence[str]:
        lines = text.splitlines()
        if max_width is None:
            return lines
        font = truetype(self.font, self.size)
        res = list[str]()
        for line in lines:
            splitted = self._split_line(font, line, max_width)
            res.extend(splitted)
        return res

    @classmethod
    def of(
        cls,
        text: str,
        font: str,
        size: int = 12,
        max_width: Optional[int] = None,
        alignment: Alignment = Alignment.START,
        color: Optional[Color] = None,
        **kwargs: Unpack[BaseStyle],
    ) -> Self:
        return cls(text, font, size, max_width, alignment, color, **kwargs)

    @property
    @override
    def content_width(self) -> int:
        return max(rt.width for rt in self.pre_rendered)

    @property
    @override
    def content_height(self) -> int:
        return sum(rt.height for rt in self.pre_rendered)

    @override
    def render_content(self) -> RenderImage:
        return RenderImage.concat(
            self.pre_rendered,
            direction=Direction.VERTICAL,
            alignment=self.alignment,
            color=self.background,
        )
