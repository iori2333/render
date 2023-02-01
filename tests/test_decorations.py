from render import *

from data import Font, Output

deco_dir = Output / "deco"
deco_dir.mkdir(exist_ok=True)


def test_crop():
    decorations = Decorations.of().after_padding(
        RectCrop.of(border_radius=20, box_sizing=BoxSizing.BORDER_BOX),
        Contour.of(Palette.GRAY, thickness=1),
    )
    obj = Image.from_color(
        100,
        80,
        Palette.AQUA,
        padding=Space.of_side(10, 8),
        margin=Space.all(10),
        decorations=decorations,
        background=Palette.WHITE,
    )
    im1 = obj.render()
    decorations = Decorations.of().after_padding(
        CircleCrop(radius=45, box_sizing=BoxSizing.BORDER_BOX),
        Contour.of(Palette.GRAY, thickness=1),
    )
    obj.decorations = decorations
    im2 = obj.render()
    RenderImage.concat_vertical(
        [im1, im2],
        alignment=Alignment.CENTER,
    ).save(deco_dir / "crop.png")


def test_grayscale():
    im1 = RenderImage.empty(50, 50, color=Palette.BLUE)
    im2 = RenderImage.empty(20, 20, color=Palette.GREEN)
    im3 = RenderImage.empty(100, 100, color=Palette.RED)
    el1, el2, el3 = map(Image.from_image, (im1, im2, im3))
    grayscale = Grayscale.of()
    container = FixedContainer.from_children(
        width=200,
        height=150,
        children=[el1, el2, el3],
        alignment=Alignment.CENTER,
        justify_content=JustifyContent.SPACE_AROUND,
        border=Border.of(5, Palette.ORANGE),
        padding=Space.all(20),
        margin=Space.all(20),
        background=Palette.ANTIQUE_WHITE,
        decorations=[grayscale],
    )

    images = []
    for box in [
            BoxSizing.CONTENT_BOX,
            BoxSizing.PADDING_BOX,
            BoxSizing.BORDER_BOX,
            BoxSizing.FULL_BOX,
    ]:
        grayscale.box_sizing = box
        images.append(container.render())
    RenderImage.concat_vertical(
        images,
        alignment=Alignment.CENTER,
    ).save(deco_dir / "grayscale-box.png")

    images = []
    for amount in range(11):
        grayscale.amount = amount / 10.0
        images.append(container.render())
    RenderImage.concat_vertical(
        images,
        alignment=Alignment.CENTER,
    ).save(deco_dir / "grayscale-amount.png")


def test_box_shadow():
    text1 = Text.of("31", Font.get("YAHEI"), 64, color=Palette.WHITE)
    text2 = Text.of(
        "January 31, 2023",
        Font.get("YAHEI"),
        16,
        color=Palette.BLACK,
        padding=Space.all(10),
    )
    container = Container.from_children(
        [
            FixedContainer.from_children(
                250,
                250,
                [text1],
                alignment=Alignment.CENTER,
                justify_content=JustifyContent.CENTER,
                background=Color.of_hex("#4CAF50"),
            ),
            text2,
        ],
        direction=Direction.VERTICAL,
        alignment=Alignment.CENTER,
        background=Palette.WHITE,
        decorations=[
            BoxShadow.of(blur_radius=51,
                         spread=4,
                         color=Color.of(0, 0, 0, 0.8))
        ],
        margin=Space.all(50),
    )
    Container.from_children(
        [container],
        padding=Space.all(10),
        background=Palette.WHITE,
    ).render().save(deco_dir / "shadow-box.png")


def test_text_shadow():
    style = TextStyle.of(
        font=Font.get("YAHEI"),
        size=64,
        color=Palette.BLACK,
    )
    shadow = ContentShadow.of((3, 3),
                              blur_radius=10,
                              color=Palette.BLACK.of_alpha(128))
    text = Text.from_style(
        "Hello World",
        style=style,
        decorations=Decorations.of().after_content(shadow),
        background=Palette.WHITE,
    )
    im1 = text.render()

    text.color = Palette.WHITE
    shadow.offset = (0, 0)
    shadow.blur_radius = 51
    shadow.color = Palette.GREEN
    im2 = text.render()
    RenderImage.concat_vertical([im1, im2], alignment=Alignment.CENTER).save(
        deco_dir / "shadow-text.png")
