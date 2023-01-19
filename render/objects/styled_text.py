import re
from typing import Dict, Generator, Iterable, List, Optional, Tuple
from typing_extensions import Self, TypedDict, Unpack, override

from PIL import ImageFont

from render.base import (Alignment, BaseStyle, Color, Direction, Palette,
                         RenderImage, RenderObject, RenderText)
from render.utils import PathLike
from .text import Text


class TextStyle(TypedDict, total=False):
    font: PathLike
    size: int
    color: Optional[Color]
    stroke_width: int
    stroke_color: Optional[Color]
    background: Optional[Color]
    hyphenation: bool


class NestedTextStyle:
    def __init__(self) -> None:
        self.stack: List[Tuple[str, TextStyle]] = []

    def push(self, name: str, style: TextStyle) -> None:
        self.stack.append((name, style))

    def pop(self, name: str) -> TextStyle:
        if not self.stack:
            raise ValueError("Empty stack")
        pop, style = self.stack.pop()
        if pop != name:
            raise ValueError(f"Unmatched tag: expected {pop}, got {name}")
        return style

    def query(self) -> TextStyle:
        style = TextStyle()
        for _, s in reversed(self.stack):
            for k, v in s.items():
                if k not in style or style[k] is None:
                    style[k] = v
        return style


class StyledText(RenderObject):

    tag_begin = re.compile(r"<(\w+)>")
    tag_end = re.compile(r"</(\w+)>")

    def __init__(
        self,
        blocks: Iterable[Tuple[str, TextStyle]],
        max_width: Optional[int],
        alignment: Alignment,
        line_spacing: int,
        **kwargs: Unpack[BaseStyle],
    ) -> None:
        super(StyledText, self).__init__(**kwargs)

        self.max_width = max_width
        self.alignment = alignment
        self.line_spacing = line_spacing
        self.pre_rendered = [
            self.text_concat(line) for line in self.cut(blocks, max_width)
        ]

    @property
    @override
    def content_width(self) -> int:
        if self.pre_rendered:
            return max(rt.width for rt in self.pre_rendered)
        return 0

    @property
    @override
    def content_height(self) -> int:
        return (sum(rt.height for rt in self.pre_rendered) +
                self.line_spacing * (len(self.pre_rendered) - 1))

    @override
    def render_content(self) -> RenderImage:
        return RenderImage.concat(
            self.pre_rendered,
            direction=Direction.VERTICAL,
            alignment=self.alignment,
            color=self.background,
            spacing=self.line_spacing,
        )

    def cut(
        self,
        blocks: Iterable[Tuple[str, TextStyle]],
        max_width: Optional[int],
    ) -> Generator[List[RenderText], None, None]:

        max_width = max_width or 0x80000000
        remain: List[RenderText] = []

        for block, style in blocks:
            font_path = str(style.get("font", ""))
            font_size = style.get("size", 0)
            font = ImageFont.truetype(font_path, font_size)
            stroke_width = style.get("stroke_width", 0)
            stroke_color = style.get("stroke_color", None)
            hyphenation = style.get("hyphenation", True)

            natural_lines = block.splitlines()
            for line_no, line in enumerate(natural_lines):
                remain_width = sum(r.width for r in remain)
                if max_width is None:
                    splitted = [line]
                else:
                    splitted = Text._split_line(font,
                                                line,
                                                stroke_width,
                                                max_width,
                                                hyphenation,
                                                start_width=max_width -
                                                remain_width)
                if not splitted:
                    continue
                rt = [
                    RenderText.of(
                        s,
                        font_path,
                        font_size,
                        style.get("color"),
                        stroke_width,
                        stroke_color,
                        style.get("background") or self.background,
                    ) for s in splitted
                ]
                first, *rest = rt
                if max_width is None or remain_width + first.width <= max_width:
                    remain.append(first)
                for i, r in enumerate(rest):
                    if remain:
                        yield remain
                        remain = []
                    if i == len(rest) - 1 and line_no == len(
                            natural_lines) - 1:
                        remain.append(r)
                    else:
                        yield [r]
                if remain and line_no != len(natural_lines) - 1:
                    yield remain
                    remain = []
        if remain:
            yield remain

    @staticmethod
    def text_concat(text: Iterable[RenderText]) -> RenderImage:
        rendered = [text.render() for text in text]
        width = sum(text.width for text in rendered)
        height = max(text.height for text in rendered)
        baseline = max(text.baseline for text in text)
        im = RenderImage.empty(width, height, Palette.TRANSPARENT)
        x = 0
        for obj, image in zip(text, rendered):
            im = im.paste(x, baseline - obj.baseline, image)
            x += image.width
        return im

    @classmethod
    def of_tag(
        cls,
        text_with_tags: str,
        default: TextStyle,
        styles: Dict[str, TextStyle],
        max_width: Optional[int] = None,
        alignment: Alignment = Alignment.START,
        line_spacing: int = 0,
        **kwargs: Unpack[BaseStyle],
    ) -> Self:
        """Create a Text object from a string with tags.

        Args:
            text_with_tags (str): The text with html tags.
            default (TextStyle): The default text style.
            styles (Dict[str, TextStyle]): The styles for each tag.
        """
        style = NestedTextStyle()
        style.push("default", default)
        blocks: List[Tuple[str, TextStyle]] = []

        index = 0
        while index < len(text_with_tags):
            match = cls.tag_begin.match(text_with_tags, index)
            if match:
                name = match.group(1)
                style.push(name, styles[name])
                index = match.end()
                continue
            match = cls.tag_end.match(text_with_tags, index)
            if match:
                name = match.group(1)
                try:
                    style.pop(name)
                except ValueError as e:
                    raise ValueError(str(e) + " in " + repr(text_with_tags)) from e
                index = match.end()
                continue
            next_tag = text_with_tags.find("<", index)
            if next_tag == -1:
                next_tag = len(text_with_tags)
            plain_text = text_with_tags[index:next_tag]
            if plain_text:
                blocks.append((plain_text, style.query()))
            index = next_tag
        return cls(blocks, max_width, alignment, line_spacing, **kwargs)
