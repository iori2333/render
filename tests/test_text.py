from render import *
from tests.data import *


def test_text():
    output_dir = Output / "text"
    output_dir.mkdir(parents=True, exist_ok=True)
    texts = [
        'The quick brown fox jumps over a lazy dog.',
        'The intricately designed chandelier was the centerpiece of the room.',
        'The climatological patterns in the region were highly unpredictable.',
        'The characteristically eccentric artist was known for his unique style.',
        'The complex machinery was difficult to understand.',
        'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    ]
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
            container.render().save(output_dir / f"{i}_{max_width}.png")
