from time import perf_counter

from render import *

from data import Font, Output

cache_dir = Output / "cache"
cache_dir.mkdir(exist_ok=True)


def test_cache_text():
    n_rows = 10
    n_cols = 10
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

    # render 1
    im1, elapsed1 = render()
    # render cache
    _, elapsed_cache = render()
    # render 2
    hello.text = "Holla"
    hello.color = Palette.SKY_BLUE
    world.text = "Mundo"
    im2, elapsed2 = render()

    print(f"Original: {elapsed1:.4f}s")
    print(f"Cached  : {elapsed_cache:.4f}s")
    print(f"Changed : {elapsed2:.4f}s")

    RenderImage.concat_horizontal(
        [im1, im2],
        alignment=Alignment.CENTER,
    ).save(cache_dir / "text.png")


def test_cache_styled_text():
    default = TextStyle.of(font=Font.one(), size=24, color=Palette.ORANGE_RED)
    large = TextStyle.of(size=48)
    text = StyledText.of(
        text="<l>Hello</l> World!",
        styles={
            "default": default,
            "l": large,
        },
    )

    # render 1
    im = text.render()
    # render 2
    large.size = 96
    large.color = Palette.SEA_GREEN
    im2 = text.render()
    # render 3
    large.decoration = TextDecoration.UNDERLINE
    im3 = text.render()
    RenderImage.concat_vertical(
        [im, im2, im3],
        alignment=Alignment.CENTER,
    ).save(cache_dir / "styled-text.png")


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
                                alignment=Alignment.CENTER,
                                border=Border.of(2))

    # render 1
    im1 = stack.render()
    # render 2
    sp1.space_width, sp1.space_height = 200, 100
    sp2.space_width, sp2.space_height = 100, 200
    text1.color, text2.color = text2.color, text1.color
    im2 = stack.render()
    # render 3
    stack.vertical_alignment = Alignment.START
    im3 = stack.render()
    # render 4
    stack.vertical_alignment = Alignment.END
    im4 = stack.render()
    RenderImage.concat_vertical(
        [im1, im2, im3, im4],
        alignment=Alignment.CENTER,
        spacing=5,
    ).save(cache_dir / "stack.png")


def test_cache_relative():
    # set up a container with three children
    red = Image.from_color(50, 50, Palette.RED)
    green = Image.from_color(150, 150, Palette.GREEN)
    blue = Image.from_color(25, 25, Palette.BLUE)
    container = RelativeContainer(border=Border.of(2))
    container.add_child(red, align_left=container, align_top=container)
    container.add_child(blue,
                        center_horizontal=container,
                        center_vertical=container)
    container.add_child(green, align_right=container, align_bottom=container)
    container.add_constraint(blue, right=red, below=red)
    container.add_constraint(green, right=blue, below=blue)
    # render 1
    im1 = container.render()
    # render 2
    blue.im = RenderImage.empty(100, 100, Palette.AQUA)
    im2 = container.render()
    # render 3
    center = Image.from_color(5, 5, Palette.RED)
    half = Image.from_color(1, 1, Palette.RED)
    quarter = Image.from_color(1, 1, Palette.RED)
    container.set_offset(blue, (25, 25)).add_child(
        center,
        center=container,
        prior_to=blue,
    ).add_child(
        half,
        center=center,
        offset=(25, 0),
    ).add_child(
        quarter,
        center=half,
        offset=(25, 0),
    )
    im3 = container.render()
    # compare results
    RenderImage.concat_vertical(
        [im1, im2, im3],
        alignment=Alignment.CENTER,
        spacing=5,
    ).save(cache_dir / "relative.png")
