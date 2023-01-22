from render import *
from tests.data import *

alpha = 170


def test_stack_bg_when_deco():
    """This test will fail if background is used 
    for stack.render_content to create empty canvas."""

    x = Stack.from_children([],
                            background=Color.of(0, 0, 0, alpha),
                            padding=Space.all(10),
                            decorations=[
                                RectCrop.of(border_radius=5,
                                            box_sizing=BoxSizing.FULL_BOX)
                            ])
    arr = x.render().base_im
    y = arr.shape[0] // 2
    x = arr.shape[1] // 2
    assert (arr[y, x] == (0, 0, 0, alpha)).all(), \
    f"{arr[y, x]} should be (0, 0, 0, {alpha})"


def test_text_bg():
    text = Text.of(" ",
                   Font.one(),
                   background=Color.of(0, 0, 0, alpha),
                   color=Palette.TRANSPARENT)
    arr = text.render().base_im
    y = arr.shape[0] // 2
    x = arr.shape[1] // 2
    assert (arr[y, x] == (0, 0, 0, alpha)).all(), \
    f"{arr[y, x]} should be (0, 0, 0, {alpha})"
