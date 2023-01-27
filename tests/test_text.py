from itertools import cycle
from render import *
from tests.data import *

texts = [
    'The quick brown fox jumps over a lazy dog.',
    'The intricately designed chandelier was the centerpiece of the room.',
    'The climatological patterns in the region were highly unpredictable.',
    'The characteristically eccentric artist was known for his unique style.',
    'The complex machinery was difficult to understand.',
    'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
]

texts_with_tag = [
    '<0>The quick <1>brown</1> fox jumps over</0> a lazy dog.',
    'The intricately designed <1>chan</1>delier was the center<2>piece</2> of the room.',
    'The <0>climatological <1>patterns</1> in the <2>region were highly un</2>predictable.</0>',
    'The charac<3>teristically ecc</3>entric artist was known for his unique style.',
    'The complex <2>machinery was diffi</2>cult to understand.',
    'aaaa<0>a</0><1>a</1>a<2>aaaaaaaaaaaaaaaaaaaa<3>aaaaaaaaaaa</3>aaaaaaaaaaaaa</2>aa',
]

fonts = cycle(Font.fonts())

styles = {
    str(i): TextStyle.of(font=next(fonts),
                         size=sz,
                         color=Color.rand(),
                         background=Color.rand(),
                         hyphenation=True)
    for i, sz in enumerate(range(32, 64, 8))
}

default = TextStyle.of(font=next(fonts), size=36, color=Palette.BLACK)

output_dir = Output / "text"
output_dir.mkdir(parents=True, exist_ok=True)


def test_text():
    for max_width in [None, 100, 200, 300, 400, 500]:
        for i, text in enumerate(texts):
            container = Container.from_children(
                children=[
                    Text.of(text,
                            font=font,
                            size=sz,
                            max_width=max_width,
                            color=Palette.BLACK,
                            line_spacing=sz // 4,
                            hyphenation=True,
                            alignment=Alignment.START) for sz in [32]
                    for font in Font.fonts()
                ],
                direction=Direction.VERTICAL,
                background=Palette.ANTIQUE_WHITE,
            )
            container.render().save(output_dir / f"{i}-{max_width}.png")


def test_styled_text():
    for max_width in [None, 200, 400, 600]:
        for i, text in enumerate(texts_with_tag):
            container = Container.from_children(
                children=[
                    StyledText.of(
                        text,
                        default=default,
                        styles=styles,
                        max_width=max_width,
                        line_spacing=4,
                    )
                ],
                direction=Direction.VERTICAL,
                background=Palette.ANTIQUE_WHITE,
            )
            container.render().save(output_dir / f"style-{i}-{max_width}.png")


def test_styled_stroke():
    text = "The <1>quick</1> brown <3>fox</3> <5>jumps</5> over a lazy dog."
    default = TextStyle.of(font=Font.one(),
                           size=36,
                           color=Palette.BLACK,
                           decoration=TextDecoration.UNDERLINE)
    styles = {
        "1": TextStyle.of(stroke_width=1, stroke_color=Palette.BLUE),
        "3": TextStyle.of(stroke_width=3, stroke_color=Palette.BLUE),
        "5": TextStyle.of(stroke_width=5, stroke_color=Palette.BLUE),
    }
    StyledText.of(text, default=default,
                      styles=styles).render().save(output_dir / "stroke.png")


def test_text_decoration():
    flags = [
        TextDecoration.UNDERLINE, TextDecoration.OVERLINE,
        TextDecoration.LINE_THROUGH
    ]
    for max_width in [None, 200, 600]:
        for i, text in enumerate(texts):
            container = Container.from_children(
                children=[
                    Text.of(text,
                            font=font,
                            size=32,
                            max_width=max_width,
                            color=Palette.BLACK,
                            line_spacing=6,
                            hyphenation=True,
                            text_decoration=flags[i % len(flags)],
                            text_decoration_thickness=-1 if j % 2 == 0 else 1,
                            alignment=Alignment.START)
                    for j, font in enumerate(Font.fonts())
                ],
                direction=Direction.VERTICAL,
                background=Palette.ANTIQUE_WHITE,
            )
            container.render().save(output_dir / f"{i}-{max_width}-deco.png")
