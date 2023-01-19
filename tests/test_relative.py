from render import *
from tests.data import *
from tests.utils import *


def test_relative_prior():
    red = TestRect.of(100, 100, Palette.RED)
    green = TestRect.of(300, 300, Palette.GREEN)
    blue = TestRect.of(50, 50, Palette.BLUE)
    black = TestRect.of(30, 30, Palette.BLACK)
    yellow = TestRect.of(40, 40, Color.of(255, 255, 0))

    def make_relative(prior: bool = False):
        container = RelativeContainer(background=Palette.TRANSPARENT)
        container.add_child(
            red,
            align_left=container,
            align_top=container,
        )
        container.add_child(
            green,
            right=red,
            below=red,
        )
        container.add_child(
            blue,
            center_horizontal=green,
            center_vertical=red,
        )
        if prior:
            container.add_child(
                black,
                align_top=container,
                align_right=blue,
            )
            container.add_child(yellow,
                                align_top=container,
                                align_left=blue,
                                prior_to=black)
        else:
            container.add_child(
                black,
                align_top=container,
                align_right=blue,
                prior_to=yellow,
            )
            container.add_child(
                yellow,
                align_top=container,
                align_left=blue,
            )
        return container

    prior, no_prior = make_relative(prior=True), make_relative(prior=False)
    Container.from_children([prior, no_prior
                             ]).render().save(Output / "relative-prior.png")


def test_relative_out_of_canvas():
    red = TestRect.of(100, 100, Palette.RED)
    green = TestRect.of(300, 300, Palette.GREEN)
    blue = TestRect.of(50, 50, Palette.BLUE)
    container = RelativeContainer()
    container.add_child(red, align_left=container, align_top=container)
    container.add_child(green, right=red, below=red)
    container.add_child(blue, left=red, above=red)
    container.render().save(Output / "relative-out-of-canvas.png")


def test_relative_out_of_canvas2():
    red = TestRect.of(100, 100, Palette.RED.of_alpha(64))
    green = TestRect.of(300, 300, Palette.GREEN.of_alpha(64))
    blue = TestRect.of(50, 50, Palette.BLUE.of_alpha(64))
    black = TestRect.of(250, 250, Palette.BLACK)
    container = RelativeContainer()
    container.add_child(red,
                        center_horizontal=container,
                        center_vertical=container,
                        prior_to=green)
    container.add_child(green,
                        center_horizontal=container,
                        center_vertical=container,
                        prior_to=blue)
    container.add_child(blue,
                        center_horizontal=container,
                        center_vertical=container)
    container.add_child(black, left=red, center_vertical=red)
    container.render().save(Output / "relative-out-of-canvas2.png")


def test_relative_failure():
    red = TestRect.of(100, 100, Palette.RED)
    green = TestRect.of(300, 300, Palette.GREEN)
    container = RelativeContainer()
    container.add_child(red, align_left=container, align_top=container)
    container.add_child(green, align_right=container, align_bottom=container)
    try:
        container.render()
    except ValueError as e:
        print("ValueError successfully raised: " + str(e))
    else:
        assert 0, "Expected ValueError"
