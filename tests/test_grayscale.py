from render import (Alignment, Border, BoxSizing, FixedContainer, Grayscale,
                    Image, JustifyContent, Palette, RenderImage, Space)

from data import Output


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
    RenderImage.concat_vertical(images, alignment=Alignment.CENTER).save(
        Output / "grayscale-box-sizing.png")

    images = []
    for amount in range(11):
        grayscale.amount = amount / 10.0
        images.append(container.render())
    RenderImage.concat_vertical(images, alignment=Alignment.CENTER).save(
        Output / "grayscale-amount.png")
