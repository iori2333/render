import re
from typing import Dict, Generator, Iterable, List, Optional, Tuple
from typing_extensions import Self, TypedDict, Unpack, override

from PIL import ImageFont

from render.base import (Alignment, BaseStyle, Color, Direction, Palette,
                         RenderImage, RenderObject, RenderText, TextDecoration)
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
    decoration: TextDecoration
    decoration_thickness: int


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
                self.line_spacing * max(len(self.pre_rendered) - 1, 0))

    @override
    def render_content(self) -> RenderImage:
        return RenderImage.concat(
            self.pre_rendered,
            direction=Direction.VERTICAL,
            alignment=self.alignment,
            spacing=self.line_spacing,
        )

    def cut(
        self,
        blocks: Iterable[Tuple[str, TextStyle]],
        max_width: Optional[int],
    ) -> Generator[List[RenderText], None, None]:
        """Cut the text into lines. Each line is a list of RenderTexts."""

        def current_width():
            """Return the current acceptable width of the line."""
            if max_width is None:
                return None
            return max_width - sum(t.width for t in line_buffer)

        def flush(
            buffer: List[RenderText]
        ) -> Generator[List[RenderText], None, None]:
            if buffer:
                buffer[-1].text = buffer[-1].text.rstrip(" ")
            yield buffer
            buffer.clear()

        line_buffer: List[RenderText] = []
        for block, style in blocks:
            # load style properties
            font_path = str(style.get("font", ""))
            font_size = style.get("size", 0)
            font = ImageFont.truetype(font_path, font_size)
            stroke_width = style.get("stroke_width", 0)
            stroke_color = style.get("stroke_color", None)
            hyphenation = style.get("hyphenation", True)
            decoration = style.get("decoration", TextDecoration.NONE)
            decoration_thickness = style.get("decoration_thickness", -1)
            
            line_break_at_end = block.endswith('\n')
            lines = block.split('\n')
            for lineno, line in enumerate(lines):
                while line:
                    try:
                        split, remain, bad = Text._split_once(
                            font, line, stroke_width, current_width(),
                            hyphenation)
                    except ValueError:
                        # too long to fit, flush the line and try again
                        yield from flush(line_buffer)
                        split, remain, bad = Text._split_once(
                            font, line, stroke_width, current_width(),
                            hyphenation)
                    if line_buffer and bad:
                        # flush the line and try again
                        yield from flush(line_buffer)
                        split, remain, _ = Text._split_once(
                            font, line, stroke_width, current_width(),
                            hyphenation)

                    line_buffer.append(
                        RenderText.of(
                            split.lstrip(" ") if not line_buffer else split,
                            font_path,
                            font_size,
                            style.get("color"),
                            stroke_width,
                            stroke_color,
                            decoration,
                            decoration_thickness,
                            background=style.get("background")
                            or Palette.TRANSPARENT,
                        ))
                    line = remain
                # end of natural line
                if lineno != len(lines) - 1 or line_break_at_end:
                    yield from flush(line_buffer)
        # check buffer not empty
        if line_buffer:
            yield from flush(line_buffer)

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
        text: str,
        default: TextStyle,
        styles: Dict[str, TextStyle],
        max_width: Optional[int] = None,
        alignment: Alignment = Alignment.START,
        line_spacing: int = 0,
        **kwargs: Unpack[BaseStyle],
    ) -> Self:
        """Create a Text object from a string with tags.

        Args:
            text (str): The text with html tags.
            default (TextStyle): The default text style.
            styles (Dict[str, TextStyle]): The styles for each tag.
        """
        style = NestedTextStyle()
        style.push("default", default)
        blocks: List[Tuple[str, TextStyle]] = []

        index = 0
        while index < len(text):
            match = cls.tag_begin.match(text, index)
            if match:
                name = match.group(1)
                style.push(name, styles[name])
                index = match.end()
                continue
            match = cls.tag_end.match(text, index)
            if match:
                name = match.group(1)
                try:
                    style.pop(name)
                except ValueError as e:
                    raise ValueError(str(e) + " in " + repr(text)) from e
                index = match.end()
                continue
            next_tag = text.find("<", index)
            if next_tag == -1:
                next_tag = len(text)
            plain_text = text[index:next_tag]
            if plain_text:
                blocks.append((plain_text, style.query()))
            index = next_tag
        return cls(blocks, max_width, alignment, line_spacing, **kwargs)
