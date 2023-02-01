from render import (Alignment, BoxSizing, CircleCrop, Contour, Decorations,
                    Image, Palette, RectCrop, RenderImage, Space)

from data import Output


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
    RenderImage.concat_vertical([im1, im2], alignment=Alignment.CENTER).save(
        Output / "crop.png")
