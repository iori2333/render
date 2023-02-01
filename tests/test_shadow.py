from render import *

from data import Font, Output


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
    ).render().save(Output / "box_shadow.png")


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
        Output / "text_shadow.png")
