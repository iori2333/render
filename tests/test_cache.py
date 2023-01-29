from time import perf_counter

from tests.data import Font, Output

# set False and switch to master branch to test, or
# set True and switch to cache branch to test
USE_CACHE_VERSION = True

n_rows = 10
n_cols = 10


def test_text_with_cache():

    hello = Text.of("Hello", Font.one(), 48, color=Palette.AQUA)
    world = Text.of("World", Font.one(), 48, color=Palette.ALICE_BLUE)

    container1 = Container.from_children([hello, world],
                                         direction=Direction.HORIZONTAL,
                                         alignment=Alignment.CENTER,
                                         background=Palette.ANTIQUE_WHITE)
    container2 = Container.from_children([world, hello],
                                         direction=Direction.HORIZONTAL,
                                         alignment=Alignment.CENTER,
                                         background=Palette.NAVAJO_WHITE)

    container = Container.from_children([container1, container2],
                                        direction=Direction.VERTICAL,
                                        alignment=Alignment.CENTER)

    row = Container.from_children([container] * n_cols,
                                  direction=Direction.HORIZONTAL)
    square = Container.from_children([row] * n_rows,
                                     direction=Direction.VERTICAL)

    def render():
        tik = perf_counter()
        im = square.render()
        tok = perf_counter()
        return im, tok - tik

    im1, elapsed1 = render()
    _, elapsed_cache = render()

    if USE_CACHE_VERSION:
        hello.text = "Holla"
        hello.color = Palette.SKY_BLUE
    else:
        hello.update("Holla", Palette.SKY_BLUE)
    im2, elapsed2 = render()

    im1.save(Output / "cache-hello.png")
    im2.save(Output / "cache-holla.png")

    print(f"Original: {elapsed1:.4f}s")
    print(f"Cached  : {elapsed_cache:.4f}s")
    print(f"Changed : {elapsed2:.4f}s")


if USE_CACHE_VERSION:
    from render import *
else:
    import string
    from functools import lru_cache
    from typing import Optional, Sequence, Tuple

    import pyphen
    from PIL.ImageFont import FreeTypeFont, truetype
    from typing_extensions import Self, Unpack, override

    from render.base import (Alignment, BaseStyle, Color, Direction,
                             RenderImage, RenderObject, RenderText,
                             TextDecoration, Palette)
    from render.objects import Container
    from render.utils import PathLike, find_rightmost

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
            text_decoration: TextDecoration,
            text_decoration_thickness: int,
            **kwargs: Unpack[BaseStyle],
        ) -> None:
            super(Text, self).__init__(**kwargs)

            self.text = text
            self.color = color
            self.stroke_width = stroke_width
            self.stroke_color = stroke_color
            self.text_decoration = text_decoration
            self.text_decoration_thickness = text_decoration_thickness
            self.max_width = max_width

            self.font = font
            self.size = size
            self.alignment = alignment
            self.line_spacing = line_spacing
            self.hyphenation = hyphenation
            self.pre_rendered = [
                RenderText.of(line, font, size, color, stroke_width,
                              stroke_color, text_decoration,
                              text_decoration_thickness,
                              self.background).render()
                for line in self.cut(text, stroke_width, max_width)
            ]

        def update(self, text: str, color: Optional[Color]) -> Self:
            self.text = text
            self.color = color
            self.pre_rendered = [
                RenderText.of(line, self.font, self.size, color,
                              self.stroke_width, self.stroke_color,
                              self.text_decoration,
                              self.text_decoration_thickness,
                              self.background).render()
                for line in self.cut(text, self.stroke_width, self.max_width)
            ]
            return self

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
            max_width: Optional[int],
            hyphenation: bool,
        ) -> Tuple[str, str, bool]:
            bad_split = False
            if max_width is None:
                return text, "", bad_split
            indices = list(range(len(text)))
            bound = find_rightmost(
                indices,
                max_width,
                key=lambda k: cls._calculate_width(font, text[:k], stroke_width
                                                   ),
            )
            if cls._calculate_width(font, text[:bound],
                                    stroke_width) > max_width:
                bound -= 1
            if bound <= 0:
                raise ValueError("Text is too long to fit in the given width")
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
                            font, word, stroke_width,
                            max_width - cls._calculate_width(
                                font, text[:prev], stroke_width))
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
        def _split_line(
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
                line, remain, _ = cls._split_once(font, text, stroke_width,
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
        ):
            cuts = list(cls._dict.iterate(word))
            cuts.sort(key=lambda k: len(k[0]))
            cut_bound = find_rightmost(
                range(len(cuts)),
                max_width,
                key=lambda k: cls._calculate_width(font, cuts[k][0] + "-",
                                                   stroke_width))
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
                splitted = self._split_line(font, line, stroke_width,
                                            max_width, self.hyphenation)
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
            text_decoration: TextDecoration = TextDecoration.NONE,
            text_decoration_thickness: int = -1,
            **kwargs: Unpack[BaseStyle],
        ) -> Self:
            return cls(text, font, size, max_width, alignment, color,
                       stroke_width, stroke_color, line_spacing, hyphenation,
                       text_decoration, text_decoration_thickness, **kwargs)

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
                spacing=self.line_spacing,
            )


def test_cache_styled_text():
    default = TextStyle.of(font=Font.one(), size=24, color=Palette.ORANGE_RED)
    large = TextStyle.of(size=48)
    text = StyledText.of("<l>Hello</l> World!",
                         styles={
                             "default": default,
                             "l": large,
                         })
    image = text.render()
    large.size = 96
    image2 = text.render()
    RenderImage.concat_vertical([image, image2],
                                alignment=Alignment.CENTER).save(
                                    Output / "cache_styled_text.png")


def test_cache_stack():
    sp1 = Spacer.of(100, 200)
    sp2 = Spacer.of(200, 100)
    text1 = Text.of("Hello", font=Font.one(), size=24, color=Palette.AQUA)
    text2 = Text.of("World",
                    font=Font.one(),
                    size=24,
                    color=Palette.BLUE_VIOLET)
    container1 = Container.from_children([text1, sp1, text2],
                                         direction=Direction.HORIZONTAL,
                                         alignment=Alignment.CENTER)
    container2 = Container.from_children([text1, sp2, text2],
                                         direction=Direction.VERTICAL,
                                         alignment=Alignment.CENTER)
    stack = Stack.from_children([container1, container2],
                                alignment=Alignment.CENTER)
    im1 = stack.render()
    sp1.space_width, sp1.space_height = 200, 100
    sp2.space_width, sp2.space_height = 100, 200
    text1.color, text2.color = text2.color, text1.color
    im2 = stack.render()
    stack.vertical_alignment = Alignment.START
    im3 = stack.render()
    stack.vertical_alignment = Alignment.END
    im4 = stack.render()
    RenderImage.concat_vertical([im1, im2, im3, im4],
                                alignment=Alignment.CENTER).save(
                                    Output / "cache_stack.png")


def test_cache_relative():
    red = Image.from_color(100, 100, Palette.RED)
    green = Image.from_color(300, 300, Palette.GREEN)
    blue = Image.from_color(50, 50, Palette.BLUE)
    container = RelativeContainer(border=Border.of(1))
    container.add_child(red, align_left=container, align_top=container)
    container.add_child(blue,
                        center_horizontal=container,
                        center_vertical=container)
    container.add_child(green, align_right=container, align_bottom=container)
    # add extra constraint for size inference
    container.add_constraint(blue, right=red, below=red)
    container.add_constraint(green, right=blue, below=blue)
    im1 = container.render()

    blue.im = RenderImage.empty(200, 200, Palette.AQUA)
    im2 = container.render()

    container.set_offset(blue, (50, 50)).add_child(
        Image.from_color(4, 4, Palette.BLACK),
        center=container,
        prior_to=blue,
    )
    im3 = container.render()

    RenderImage.concat_vertical([im1, im2, im3],
                                alignment=Alignment.CENTER,
                                spacing=5).save(Output / "cache_relative.png")
