from __future__ import annotations

import string
from functools import lru_cache
from typing import Sequence

import pyphen
from PIL.ImageFont import FreeTypeFont, truetype
from typing_extensions import Self, Unpack, override

from render.base import (Alignment, BaseStyle, Color, Direction, Palette,
                         RenderImage, RenderObject, RenderText, TextDecoration,
                         cached, volatile)
from render.utils import PathLike, Undefined, bisect_right

from .style import TextStyle


class Text(RenderObject):

    MARKS = set("；：。，！？、.,!?”》;:")
    _dict = pyphen.Pyphen(lang="en_US")

    def __init__(
        self,
        text: str,
        font: PathLike,
        size: int,
        max_width: int | None,
        alignment: Alignment,
        color: Color | None,
        stroke_width: int,
        stroke_color: Color | None,
        line_spacing: int,
        hyphenation: bool,
        text_decoration: TextDecoration,
        text_decoration_thickness: int,
        shading: Color,
        **kwargs: Unpack[BaseStyle],
    ) -> None:
        super().__init__(**kwargs)
        with volatile(self):
            self.text = text
            self.font = font
            self.size = size
            self.max_width = max_width
            self.alignment = alignment
            self.line_spacing = line_spacing
            self.hyphenation = hyphenation
            self.color = color
            self.stroke_width = stroke_width
            self.stroke_color = stroke_color
            self.text_decoration = text_decoration
            self.text_decoration_thickness = text_decoration_thickness
            self.shading = shading

    @staticmethod
    @lru_cache()
    def _calculate_width(font: FreeTypeFont, text: str, stroke: int) -> int:
        w, _ = font.getsize(text, stroke_width=stroke)
        return w

    @classmethod
    def split_once(
        cls,
        font: FreeTypeFont,
        text: str,
        stroke_width: int,
        max_width: int | None,
        hyphenation: bool,
    ) -> tuple[str, str, bool]:
        bad_split = False
        if max_width is None:
            return text, "", bad_split
        indices = list(range(len(text)))
        bound = bisect_right(
            indices,
            max_width,
            key=lambda k: cls._calculate_width(font, text[:k], stroke_width),
        )
        if cls._calculate_width(font, text[:bound], stroke_width) > max_width:
            bound -= 1
        if bound <= 0:
            raise ValueError(f"Text is too long to fit in the given width: "
                             f"font_size={font.size}, text={text!r}")
        if bound == len(text):
            return text, "", bad_split

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
                        return text[:prev] + first, second + text[
                            next:], bad_split

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
            bad_split = True
        return text[:bound], text[bound:], bad_split

    @classmethod
    def split_lines(
        cls,
        font: FreeTypeFont,
        text: str,
        stroke_width: int,
        max_width: int,
        hyphenation: bool,
    ) -> Sequence[str]:
        split_lines = []
        while text:
            # ignore bad_split flag
            line, remain, _ = cls.split_once(font, text, stroke_width,
                                             max_width, hyphenation)
            if line:
                split_lines.append(line.rstrip(" "))
            text = remain.lstrip(" ")
        return split_lines

    @classmethod
    def _split_word(
        cls,
        font: FreeTypeFont,
        word: str,
        stroke_width: int,
        max_width: int,
    ) -> tuple[str, str]:
        cuts = list(cls._dict.iterate(word))
        cuts.sort(key=lambda k: len(k[0]))
        cut_bound = bisect_right(range(len(cuts)),
                                 max_width,
                                 key=lambda k: cls._calculate_width(
                                     font, cuts[k][0] + "-", stroke_width))
        if cut_bound == 0 or not cuts:
            return "", word
        return cuts[cut_bound - 1][0] + "-", cuts[cut_bound - 1][1]

    @cached
    def cut(self) -> Sequence[str]:
        lines = self.text.splitlines()
        if self.max_width is None:
            return lines
        font = truetype(str(self.font), self.size)
        res: list[str] = []
        for line in lines:
            splits = self.split_lines(font, line, self.stroke_width,
                                      self.max_width, self.hyphenation)
            res.extend(splits)
        return res

    @classmethod
    def of(
        cls,
        text: str,
        font: PathLike,
        size: int = 12,
        max_width: int | None = None,
        alignment: Alignment = Alignment.START,
        color: Color | None = None,
        stroke_width: int = 0,
        stroke_color: Color | None = None,
        line_spacing: int = 0,
        hyphenation: bool = True,
        text_decoration: TextDecoration = TextDecoration.NONE,
        text_decoration_thickness: int = -1,
        shading: Color = Palette.TRANSPARENT,
        **kwargs: Unpack[BaseStyle],
    ) -> Self:
        return cls(text, font, size, max_width, alignment, color, stroke_width,
                   stroke_color, line_spacing, hyphenation, text_decoration,
                   text_decoration_thickness, shading, **kwargs)

    @classmethod
    def from_style(
        cls,
        text: str,
        style: TextStyle,
        max_width: int | None = None,
        alignment: Alignment = Alignment.START,
        line_spacing: int = 0,
        **kwargs: Unpack[BaseStyle],
    ) -> Self:
        font = Undefined.default(style.font, "")
        font_size = Undefined.default(style.size, 0)
        color = Undefined.default(style.color, None)
        stroke_width = Undefined.default(style.stroke_width, 0)
        stroke_color = Undefined.default(style.stroke_color, None)
        hyphenation = Undefined.default(style.hyphenation, True)
        decoration = Undefined.default(style.decoration, TextDecoration.NONE)
        thick = Undefined.default(style.decoration_thickness, -1)
        shading = Undefined.default(style.shading, None)
        return cls.of(text, font, font_size, max_width, alignment, color,
                      stroke_width, stroke_color, line_spacing, hyphenation,
                      decoration, thick, shading or Palette.TRANSPARENT,
                      **kwargs)

    @property
    @cached
    @override
    def content_width(self) -> int:
        return self.render_content().width

    @property
    @cached
    @override
    def content_height(self) -> int:
        return self.render_content().height

    @cached
    @override
    def render_content(self) -> RenderImage:
        lines = [
            RenderText.of(line,
                          self.font,
                          self.size,
                          self.color,
                          self.stroke_width,
                          self.stroke_color,
                          self.text_decoration,
                          self.text_decoration_thickness,
                          shading=self.shading,
                          background=self.background).render()
            for line in self.cut()
        ]
        return RenderImage.concat(
            lines,
            direction=Direction.VERTICAL,
            alignment=self.alignment,
            spacing=self.line_spacing,
        )
