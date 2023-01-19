import string
from functools import lru_cache
from typing import Optional, Sequence, Tuple
from typing_extensions import override, Self, Unpack

import pyphen
from PIL.ImageFont import FreeTypeFont, truetype

from render.base import (RenderObject, RenderImage, RenderText, Color,
                         BaseStyle, Alignment, Direction)
from render.utils import find_rightmost, PathLike


class Text(RenderObject):

    MARKS = set("；：。，！？、.,!?”》;:")
    _dict = pyphen.Pyphen(lang="en_US")

    def __init__(
        self,
        text: str,
        font: PathLike,
        size: int,
        max_width: Optional[int],
        alignment: Alignment,
        color: Optional[Color],
        stroke_width: int,
        stroke_color: Optional[Color],
        line_spacing: int,
        hyphenation: bool,
        **kwargs: Unpack[BaseStyle],
    ) -> None:
        super(Text, self).__init__(**kwargs)

        self.font = font
        self.size = size
        self.alignment = alignment
        self.line_spacing = line_spacing
        self.hyphenation = hyphenation
        self.pre_rendered = [
            RenderText.of(line, font, size, color, stroke_width, stroke_color,
                          self.background).render()
            for line in self.cut(text, stroke_width, max_width)
        ]

    @staticmethod
    @lru_cache()
    def _calculate_width(font: FreeTypeFont, text: str, stroke: int):
        w, _ = font.getsize(text, stroke_width=stroke)
        return w

    @classmethod
    def _split_once(
        cls,
        font: FreeTypeFont,
        text: str,
        stroke_width: int,
        max_width: int,
        hyphenation: bool,
    ) -> Tuple[str, str]:
        if len(text) == 0:
            return "", ""
        indices = list(range(len(text)))
        bound = find_rightmost(
            indices,
            max_width,
            key=lambda k: cls._calculate_width(font, text[:k], stroke_width),
        )
        if cls._calculate_width(font, text[:bound], stroke_width) > max_width:
            bound -= 1
        if bound <= 0:
            raise ValueError("Text is too long to fit in the given width")
        if bound == len(text):
            return text, ""

        original_bound = bound
        # try to cut at a word boundary
        if text[bound] in string.ascii_letters:
            # search for the word boundary
            prev = next = bound
            while prev >= 0 and text[prev] in string.ascii_letters:
                prev -= 1
            while next < len(text) and text[next] in string.ascii_letters:
                next += 1
            prev += 1
            word = text[prev:next]
            if len(word) > 1:
                if not hyphenation:
                    # simply put the whole word in the next line
                    bound = prev
                else:
                    first, second = cls._split_word(
                        font, word, stroke_width, max_width -
                        cls._calculate_width(font, text[:prev], stroke_width))
                    if not first:
                        # no possible cut, put the whole word in the next line
                        bound = prev
                    else:
                        return text[:prev] + first, second + text[next:]

        # try not to leave a mark at the beginning of the next line
        if text[bound] in cls.MARKS:
            if cls._calculate_width(font, text[:bound + 1],
                                    stroke_width) <= max_width:
                bound += 1
            else:
                prev = bound - 1
                # word followed by the mark should go with it to the next line
                while prev >= 0 and text[prev] in string.ascii_letters:
                    prev -= 1
                prev += 1
                bound = prev
        # failed somewhere, give up
        if bound == 0:
            bound = original_bound
        return text[:bound].rstrip(" "), text[bound:].lstrip(" ")

    @classmethod
    def _split_line(
        cls,
        font: FreeTypeFont,
        text: str,
        stroke_width: int,
        max_width: int,
        hyphenation: bool,
        start_width: Optional[int] = None,
    ) -> Sequence[str]:
        if start_width is not None:
            try:
                line, remaining = cls._split_once(font, text, stroke_width,
                                                  start_width, hyphenation)
            except ValueError:
                line, remaining = cls._split_once(font, text, stroke_width,
                                                  max_width, hyphenation)
        else:
            line, remaining = cls._split_once(font, text, stroke_width,
                                              max_width, hyphenation)
        if not line and not remaining:
            return []
        if not remaining:
            return [line]
        return [
            line, *cls._split_line(font, remaining, stroke_width, max_width,
                                   hyphenation, None)
        ]

    @classmethod
    def _split_word(
        cls,
        font: FreeTypeFont,
        word: str,
        stroke_width: int,
        max_width: int,
    ):
        cuts = list(cls._dict.iterate(word))
        cuts.sort(key=lambda k: len(k[0]))
        cut_bound = find_rightmost(range(len(cuts)),
                                   max_width,
                                   key=lambda k: cls._calculate_width(
                                       font, cuts[k][0] + "-", stroke_width))
        if cut_bound == 0 or not cuts:
            return "", word
        return cuts[cut_bound - 1][0] + "-", cuts[cut_bound - 1][1]

    def cut(self, text: str, stroke_width: int,
            max_width: Optional[int]) -> Sequence[str]:
        lines = text.splitlines()
        if max_width is None:
            return lines
        font = truetype(str(self.font), self.size)
        res = list[str]()
        for line in lines:
            splitted = self._split_line(font, line, stroke_width, max_width,
                                        self.hyphenation)
            res.extend(splitted)
        return res

    @classmethod
    def of(
        cls,
        text: str,
        font: PathLike,
        size: int = 12,
        max_width: Optional[int] = None,
        alignment: Alignment = Alignment.START,
        color: Optional[Color] = None,
        stroke_width: int = 0,
        stroke_color: Optional[Color] = None,
        line_spacing: int = 0,
        hyphenation: bool = True,
        **kwargs: Unpack[BaseStyle],
    ) -> Self:
        return cls(text, font, size, max_width, alignment, color, stroke_width,
                   stroke_color, line_spacing, hyphenation, **kwargs)

    @property
    @override
    def content_width(self) -> int:
        return max(rt.width for rt in self.pre_rendered)

    @property
    @override
    def content_height(self) -> int:
        sp = max(0, len(self.pre_rendered) - 1) * self.line_spacing
        return sum(rt.height for rt in self.pre_rendered) + sp

    @override
    def render_content(self) -> RenderImage:
        return RenderImage.concat(
            self.pre_rendered,
            direction=Direction.VERTICAL,
            alignment=self.alignment,
            color=self.background,
            spacing=self.line_spacing,
        )
