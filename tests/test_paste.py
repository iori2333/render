import timeit
import random
from render import *
from tests.data import *
from tests.utils import TestRect


def setup(alpha_fore: int, alpha_back: int):
    im1 = TestRect.of(500, 500, Palette.RED.of_alpha(alpha_fore)).render()
    im2 = TestRect.of(1000, 1000, Palette.BLUE.of_alpha(alpha_back)).render()
    x = random.randint(0, 500)
    y = random.randint(0, 500)
    return im1, im2, x, y


def test_paste_performance():
    for f, b in [(255, 255), (0, 255), (255, 0), (128, 128)]:
        print("fore:", f, "back:", b)
        for method in ["paste", "cover", "overlay"]:
            im_fore, im_back, x, y = setup(f, b)
            t = timeit.timeit(
                f"im_back.{method}(x, y, im_fore)",
                globals=locals(),
                number=100,
            )
            print(f"{method}: {t:.3f} ms")


def test_paste_overlay():
    n = 10
    d = 100
    sp = 10
    images = [
        RenderImage.empty(d, d, Palette.AQUA.of_alpha(128)) for _ in range(n)
    ]

    def f1():
        """Initialize with a transparent background and overlay images on top of it. 
        And finally paste on a red background."""
        bg = RenderImage.empty(d * n + sp * (n - 1), d, Palette.TRANSPARENT)
        for i, im in enumerate(images):
            bg = bg.overlay(i * (d + sp) - sp, 0, im)
        x = RenderImage.empty_like(bg, Palette.RED.of_alpha(128))
        return x.paste(0, 0, bg)

    def f2():
        """Initialize with a background color and paste images on top of it."""
        bg = RenderImage.empty(d * n + sp * (n - 1), d,
                               Palette.RED.of_alpha(128))
        for i, im in enumerate(images):
            bg = bg.paste(i * (d + sp) - sp, 0, im)
        return bg

    t1 = timeit.timeit(f1, number=1000)
    t2 = timeit.timeit(f2, number=1000)
    print(f"n-overlay-1-paste: {t1:.3f} ms")
    print(f"n-paste: {t2:.3f} ms")


def test_paste_compare():
    x, y = 250, 250

    container = RelativeContainer()
    prev = container
    for method in ["paste", "cover", "overlay"]:
        im_fore, im_back, _, _ = setup(32, 128)
        w, h = im_fore.width, im_fore.height
        im_fore.base_im[w // 4:3 * w // 4, h // 4:3 * h // 4, 3] = 0

        im_back = getattr(im_back, method)(x, y, im_fore)
        image = Image.from_image(im_back)
        text = Text.of(method, font=Font.one(), size=36)
        if prev is container:
            container.add_child(image, align_left=prev, align_top=prev)
        else:
            container.add_child(image, right=prev, align_top=prev)
        container.add_child(text,
                            center_horizontal=image,
                            center_vertical=image)
        prev = image
    container.render().save(Output / "image-paste.png")


def test_stack_bg_when_deco():
    """This test will fail if background is used 
    for stack.render_content to create empty canvas."""
    x = Stack.from_children([],
                            background=Color.of(0, 0, 0, 170),
                            padding=Space.all(10),
                            decorations=[
                                RectCrop.of(border_radius=5,
                                            box_sizing=BoxSizing.FULL_BOX)
                            ])
    arr = x.render().base_im
    y = arr.shape[0] // 2
    x = arr.shape[1] // 2
    assert (arr[y, x] == (0, 0, 0,
                          170)).all(), f"{arr[y, x]} should be (0, 0, 0, 170)"
