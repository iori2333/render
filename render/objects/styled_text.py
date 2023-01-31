from __future__ import annotations

import re
from typing import Generator, Iterable
from typing_extensions import Self, Unpack, override

from PIL import ImageFont

from render.base import (Alignment, BaseStyle, Cacheable, Color, Palette,
                         RenderImage, RenderObject, RenderText, TextDecoration,
                         cached, volatile)
from render.utils import PathLike, Undefined, undefined
from .text import Text


class TextStyle(Cacheable):

    def __init__(
        self,
        font: PathLike | Undefined,
        size: int | Undefined,
        color: Color | None | Undefined,
        stroke_width: int | Undefined,
        stroke_color: Color | None | Undefined,
        shading: Color | Undefined,
        hyphenation: bool | Undefined,
        decoration: TextDecoration | Undefined,
        decoration_thickness: int | Undefined,
    ) -> None:
        super().__init__()
        with volatile(self):
            self.font = font
            self.size = size
            self.color = color
            self.stroke_width = stroke_width
            self.stroke_color = stroke_color
            self.shading = shading
            self.hyphenation = hyphenation
            self.decoration = decoration
            self.decoration_thickness = decoration_thickness

    @classmethod
    def of(
        cls,
        font: PathLike | Undefined = undefined,
        size: int | Undefined = undefined,
        color: Color | None | Undefined = undefined,
        stroke_width: int | Undefined = undefined,
        stroke_color: Color | None | Undefined = undefined,
        background: Color | Undefined = undefined,
        hyphenation: bool | Undefined = undefined,
        decoration: TextDecoration | Undefined = undefined,
        decoration_thickness: int | Undefined = undefined,
    ) -> Self:
        return cls(
            font,
            size,
            color,
            stroke_width,
            stroke_color,
            background,
            hyphenation,
            decoration,
            decoration_thickness,
        )

    def items(self) -> Generator[tuple[str, object], None, None]:
        for k, v in self.__dict__.items():
            if v is not undefined:
                yield k, v


class NestedTextStyle:

    def __init__(self) -> None:
        self.stack: list[tuple[str, TextStyle]] = []

    def push(self, name: str, style: TextStyle) -> None:
        self.stack.append((name, style))

    def pop(self, name: str) -> TextStyle:
        if not self.stack:
            raise ValueError(f"Expected tag: {name}")
        pop, style = self.stack.pop()
        if pop != name:
            raise ValueError(f"Unmatched tag: expected {pop}, got {name}")
        return style

    def query(self) -> TextStyle:
        style = TextStyle.of()
        for _, s in reversed(self.stack):
            for k, v in s.items():
                if getattr(style, k) is undefined:
                    setattr(style, k, v)
        return style


class StyledText(RenderObject):

    tag_begin = re.compile(r"<(\w+)>")
    tag_end = re.compile(r"</(\w+)>")
    tag_any = re.compile(r"</?(\w+)>")

    def __init__(
        self,
        text: str,
        styles: dict[str, TextStyle],
        max_width: int | None,
        alignment: Alignment,
        line_spacing: int,
        **kwargs: Unpack[BaseStyle],
    ) -> None:
        super().__init__(**kwargs)

        with volatile(self) as v:
            self.text = text
            self.styles = v.dict(styles)
            self.alignment = alignment
            self.line_spacing = line_spacing
            self.max_width = max_width

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

    @override
    def render_content(self) -> RenderImage:
        rendered_lines = []
        for line in self.cut():
            rendered_lines.append(self.text_concat(line))
        return RenderImage.concat_vertical(
            rendered_lines,
            alignment=self.alignment,
            spacing=self.line_spacing,
        )

    def _cut_blocks(self) -> Generator[tuple[str, TextStyle], None, None]:
        text = self.text
        styles = self.styles

        style = NestedTextStyle()
        style.push("default", self.styles["default"])

        index = 0
        while index < len(text):
            # search for tag begin,
            # if found, push the style referenced by the tag
            match = self.tag_begin.match(text, index)
            if match:
                name = match.group(1)
                if name not in styles:
                    raise ValueError(f"Style {name} used but not defined")
                style.push(name, styles[name])
                index = match.end()
                continue
            # search for tag end,
            # if found, pop the style referenced by the tag
            match = self.tag_end.match(text, index)
            if match:
                name = match.group(1)
                try:
                    style.pop(name)
                except ValueError as e:
                    raise ValueError(str(e) + " in " + repr(text)) from e
                index = match.end()
                continue
            # search for text from current index to next tag
            # next_tag = text.find("<", index)
            match = self.tag_any.search(text, index)
            next_tag = match.start() if match else -1
            if next_tag == -1:
                next_tag = len(text)
            plain_text = text[index:next_tag]
            if plain_text:
                yield plain_text, style.query()
            index = next_tag

        if len(style.stack) > 1:  # check if all tags are closed
            raise ValueError(f"Unclosed tag: {style.stack[-1][0]}")

    def cut(self) -> Generator[list[RenderText], None, None]:
        """Cut the text into lines. Each line is a list of RenderTexts."""

        def current_width():
            """Return the current acceptable width of the line."""
            if max_width is None:
                return None
            return max_width - sum(t.width for t in line_buffer)

        def flush(
            buffer: list[RenderText]
        ) -> Generator[list[RenderText], None, None]:
            """Yield the current line and clear the buffer."""
            if buffer:
                buffer[-1].text = buffer[-1].text.rstrip(" ")
            yield buffer
            buffer.clear()

        max_width = self.max_width
        blocks = self._cut_blocks()
        line_buffer: list[RenderText] = []
        for block, style in blocks:
            # load style properties
            font_path = Undefined.default(str(style.font), "")
            font_size = Undefined.default(style.size, 0)
            font = ImageFont.truetype(font_path, font_size)
            color = Undefined.default(style.color, None)
            stroke_width = Undefined.default(style.stroke_width, 0)
            stroke_color = Undefined.default(style.stroke_color, None)
            hyphenation = Undefined.default(style.hyphenation, True)
            decoration = Undefined.default(style.decoration,
                                           TextDecoration.NONE)
            thick = Undefined.default(style.decoration_thickness, -1)
            shading = Undefined.default(style.shading, None)

            line_break_at_end = block.endswith('\n')
            lines = block.split('\n')
            for lineno, line in enumerate(lines):
                while line:
                    try:
                        split, remain, bad = Text.split_once(
                            font, line, stroke_width, current_width(),
                            hyphenation)
                    except ValueError:
                        # too long to fit, flush the line and try again
                        yield from flush(line_buffer)
                        split, remain, bad = Text.split_once(
                            font, line, stroke_width, current_width(),
                            hyphenation)
                    if line_buffer and bad:
                        # flush the line and try again
                        yield from flush(line_buffer)
                        split, remain, _ = Text.split_once(
                            font, line, stroke_width, current_width(),
                            hyphenation)

                    line_buffer.append(
                        RenderText.of(
                            split.lstrip(" ") if not line_buffer else split,
                            font_path,
                            font_size,
                            color,
                            stroke_width,
                            stroke_color,
                            decoration,
                            thick,
                            shading=shading or Palette.TRANSPARENT,
                            background=self.background,
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
    def of(
        cls,
        text: str,
        styles: dict[str, TextStyle],
        default: TextStyle | None = None,
        max_width: int | None = None,
        alignment: Alignment = Alignment.START,
        line_spacing: int = 0,
        **kwargs: Unpack[BaseStyle],
    ) -> Self:
        """Create a Text object from a string with tags.

        Args:
            text: The text to render with tags to specify style.
            default: The default text style. Can be specified along with styles.
            styles: Mapping from tag to style.
            max_width: The maximum width of the text. None for no limit.
            alignment: The alignment of the text.
            line_spacing: The spacing between lines.

        Raises:
            ValueError: If the default style is not correctly specified.

        Example:
            >>> text = StyledText.of(
            ...     "Hello <b>world</b>!",
            ...     default=TextStyle(color=Palette.RED),
            ...     styles={"b": TextStyle(color=Palette.BLUE)},
            ... )
        """

        if default is not None:
            if "default" in styles:
                raise ValueError("Cannot specify default style twice")
            styles = {**styles, "default": default}
        elif "default" not in styles:
            raise ValueError("Missing default style")

        return cls(text, styles, max_width, alignment, line_spacing, **kwargs)
