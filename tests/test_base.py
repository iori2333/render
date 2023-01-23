import cv2
from render import *
from tests.data import *
from tests.utils import TestRect


def make_color_rect(name: str,
                    color: Color,
                    size: int = 160,
                    use_stack: bool = True) -> RenderObject:
    font = Font.get("Genshin")
    name = name.replace("_", " ").title()
    name = name or str(color.to_rgb())
    color_rect = TestRect.of(size, size, color)
    color_name = Text.of(name.replace("_", " ").title(),
                         font=font,
                         size=18,
                         alignment=Alignment.CENTER,
                         background=color,
                         hyphenation=False,
                         max_width=size - 10)
    color_hex = Text.of(color.as_hex(), font=font, size=8, background=color)
    if use_stack:
        spacing = TestRect.of(size // 16, size // 16, Palette.TRANSPARENT)
        color_text = Container.from_children([color_name, spacing, color_hex],
                                             direction=Direction.VERTICAL,
                                             alignment=Alignment.CENTER)
        stack = Stack.from_children([color_rect, color_text],
                                    alignment=Alignment.CENTER)
        return stack
    else:
        container = RelativeContainer(background=Palette.TRANSPARENT)
        container.add_child(color_rect,
                            center_horizontal=container,
                            center_vertical=container)
        container.add_child(
            color_name,
            center_horizontal=container,
            center_vertical=container,
            prior_to=color_rect,
        )
        container.add_child(color_hex,
                            center_horizontal=container,
                            below=color_name,
                            prior_to=color_rect,
                            offset=(0, size // 16))
        return container


def _test_color(use_stack: bool = True):
    colors = list(Palette.colors())
    n = len(colors)
    x = round(n**0.5 + 1)

    children = []
    row = []
    for i, (name, color) in enumerate(colors):
        row.append(make_color_rect(name, color, use_stack=use_stack))
        if (i + 1) % x == 0:
            children.append(
                Container.from_children(row, direction=Direction.HORIZONTAL))
            row = []
    if row:
        children.append(
            Container.from_children(row, direction=Direction.HORIZONTAL))
    container = Container.from_children(children, direction=Direction.VERTICAL)

    name = "stack" if use_stack else "relative"
    container.render().save(Output / "color-{}.png".format(name))


def test_color():
    _test_color(use_stack=True)
    _test_color(use_stack=False)


def test_resize():
    text = Text.of("Hello World", font=Font.one(), size=24)
    im1 = text.render().resize(width=300, interpolation=Interpolation.NEAREST)
    im2 = text.render().resize(width=300, interpolation=Interpolation.BILINEAR)
    im3 = text.render().resize(height=200, interpolation=Interpolation.AREA)
    im4 = text.render().resize(height=200, interpolation=Interpolation.BICUBIC)
    im5 = text.render().resize(100, 100, interpolation=Interpolation.LANCZOS)

    Container.from_children(
        [Image.from_image(im) for im in [im1, im2, im3, im4, im5]],
        direction=Direction.VERTICAL,
    ).render().save(Output / "resize.png")


def test_image():
    try:
        RenderImage.from_file("path/to/not-exist.png")
    except IOError as e:
        print("IOError successfully raised: {}".format(e))
    else:
        assert 0, "Expected IOError"

    im1 = RenderImage.from_file("assets/out.png")
    im2 = RenderImage.from_raw(cv2.cvtColor(im1.base_im, cv2.COLOR_RGBA2RGB))
    im3 = RenderImage.empty_like(im1, color=Color.rand())
    im1.save(Output / "image-out.png")
    im2.save(Output / "image-out-rgb.png")
    im3.save(Output / "image-empty.png")

    try:
        RenderImage.from_raw(cv2.cvtColor(im1.base_im, cv2.COLOR_RGBA2GRAY))
    except ValueError as e:
        print("ValueError successfully raised: {}".format(e))
    else:
        assert 0, "Expected ValueError"


def test_padding():
    container = Container.from_children(
        children=[
            Image.from_color(i * 20 + 10, 20, color=Color.rand())
            for i in range(3)
        ],
        direction=Direction.VERTICAL,
        alignment=Alignment.CENTER,
        border=Border.of(5, Palette.ANTIQUE_WHITE),
        padding=Space.horizontal(10),
        background=Palette.BLACK.of_alpha(128),
        decorations=[
            RectCrop.of(border_radius=10, box_sizing=BoxSizing.FULL_BOX)
        ])
    container.render().save(Output / "padding.png")
