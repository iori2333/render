from __future__ import annotations

from typing import Callable, Iterable, Sequence
from urllib.request import urlopen

import cv2
import numpy as np
import numpy.typing as npt
import PIL.Image as PILImage
from typing_extensions import Concatenate, Literal, ParamSpec, Self

from render.utils import ImageMask, PathLike, cast

from .color import Color, Palette
from .properties import Alignment, Border, Direction, Interpolation

_P = ParamSpec("_P")


def check_writeable(
    func: Callable[Concatenate[RenderImage, _P], RenderImage]
) -> Callable[Concatenate[RenderImage, _P], RenderImage]:

    def wrapper(self: RenderImage, *args: _P.args,
                **kwargs: _P.kwargs) -> RenderImage:
        if not self.base_im.flags.writeable:
            raise ValueError("RenderImage is read-only")
        return func(self, *args, **kwargs)

    return wrapper


class RenderImage:
    """A wrapper class for image matrices.

    Attributes:
        base_im: The image matrix (RGBA, uint8).
    """

    def __init__(self, base_im: cv2.Mat) -> None:
        self.base_im = base_im

    @classmethod
    def from_file(cls, path: PathLike) -> Self:
        """Loads an image from a file.

        RGB images are converted to RGBA with alpha channel set to 255.
        """
        im = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
        if im is None:
            raise IOError(f"Cannot load image from {path!r}")
        return cls.from_raw(im, bgr=True)

    @classmethod
    def empty(
        cls,
        width: int,
        height: int,
        color: Color = Palette.TRANSPARENT,
    ) -> Self:
        im = np.zeros((height, width, 4), dtype=np.uint8)
        im[:] = color
        return cls(im)

    @classmethod
    def empty_like(cls, im: Self, color: Color = Palette.TRANSPARENT) -> Self:
        return cls.empty(im.width, im.height, color)

    @classmethod
    def from_raw(cls, im: cv2.Mat, bgr: bool = False) -> Self:
        """Converts an image matrix to RenderImage.

        Args:
            im: The image matrix (from cv2.imread or np.array, etc.).
            bgr: Whether the image matrix is in BGR format.
        """
        if im.ndim > 3 or im.ndim < 2:
            raise ValueError(f"Invalid image shape: {im.shape}")
        channels = im.shape[2] if im.ndim == 3 else 1
        if channels == 1:
            im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGRA)
        elif channels == 3:
            im = cv2.cvtColor(im, cv2.COLOR_BGR2BGRA)
        elif channels == 4:
            pass
        else:
            raise ValueError(f"Invalid color mode: {channels}")
        if bgr:
            im = cv2.cvtColor(im, cv2.COLOR_BGRA2RGBA)
        return cls(im)

    @classmethod
    def from_pil(cls, im: PILImage.Image) -> Self:
        im = im.convert("RGBA")
        return cls.from_raw(np.array(im))

    @classmethod
    def from_url(cls, url: str) -> Self:
        with urlopen(url) as response:
            im = PILImage.open(response)
            return cls.from_pil(im)

    @classmethod
    def concat(
        cls,
        images: Iterable[Self],
        direction: Direction,
        alignment: Alignment,
        color: Color = Palette.TRANSPARENT,
        spacing: int = 0,
    ) -> Self:
        images = list(images)
        if direction == Direction.HORIZONTAL:
            return cls.concat_horizontal(images, alignment, color, spacing)
        return cls.concat_vertical(images, alignment, color, spacing)

    @classmethod
    def concat_horizontal(
        cls,
        images: Sequence[Self],
        alignment: Alignment,
        color: Color = Palette.TRANSPARENT,
        spacing: int = 0,
    ) -> Self:
        width = sum(im.width for im in images)
        width += max(0, len(images) - 1) * spacing
        height = max(im.height for im in images)
        im = cls.empty(width, height, color)
        x = 0
        for child in images:
            if alignment == Alignment.CENTER:
                y = (height - child.height) // 2
            elif alignment == Alignment.END:
                y = height - child.height
            else:
                y = 0
            im.paste(x, y, child)
            x += child.width + spacing
        return im

    @classmethod
    def concat_vertical(
        cls,
        images: Sequence[Self],
        alignment: Alignment,
        color: Color = Palette.TRANSPARENT,
        spacing: int = 0,
    ) -> Self:
        width = max(im.width for im in images)
        height = sum(im.height for im in images)
        height += max(0, len(images) - 1) * spacing
        im = cls.empty(width, height, color)
        y = 0
        for child in images:
            if alignment == Alignment.CENTER:
                x = (width - child.width) // 2
            elif alignment == Alignment.END:
                x = width - child.width
            else:
                x = 0
            im.paste(x, y, child)
            y += child.height + spacing
        return im

    @property
    def width(self) -> int:
        return self.base_im.shape[1]

    @property
    def height(self) -> int:
        return self.base_im.shape[0]

    @check_writeable
    def paste(self, x: int, y: int, im: Self) -> Self:
        """Pastes the image onto this image at the given coordinates.
        Considering alpha channels of both images.

        Based on PIL.Image.alpha_composite."""
        im_self = PILImage.fromarray(self.base_im)
        im_paste = PILImage.fromarray(im.base_im)
        im_self.alpha_composite(im_paste, (x, y))
        self.base_im = np.array(im_self)
        return self

    @check_writeable
    def cover(self, x: int, y: int, im: Self) -> Self:
        """Pastes the image onto this image at the given coordinates
        only where the cover image is not transparent.

        If the cover pixel is transparent, the pixel in the base image is not changed."""
        b, t, l, r = (y, y + im.height, x, x + im.width)
        if b >= self.height or t < 0 or l >= self.width or r < 0:
            return self
        im_cropped = im.base_im[max(-b, 0):min(self.height - b, im.height),
                                max(-l, 0):min(self.width - l, im.width)]
        # only cover where the cover image is not transparent
        mask = im_cropped[:, :, 3] != 0
        self.base_im[max(b, 0):min(t, self.height),
                     max(l, 0):min(r, self.width)][mask] = im_cropped[mask]
        return self

    @check_writeable
    def overlay(self, x: int, y: int, im: Self) -> Self:
        """Pastes the image onto this image at the given coordinates
        no matter what the alpha channel is."""
        b, t, l, r = (y, y + im.height, x, x + im.width)
        if b >= self.height or t < 0 or l >= self.width or r < 0:
            return self
        im_cropped = im.base_im[max(-b, 0):min(self.height - b, im.height),
                                max(-l, 0):min(self.width - l, im.width)]
        self.base_im[max(b, 0):min(t, self.height),
                     max(l, 0):min(r, self.width)] = im_cropped
        return self

    @check_writeable
    def set_transparency(
        self,
        start: Color = Palette.WHITE,
        end: Color = Palette.BLACK,
        spill_compensation: bool = False,
    ) -> Self:
        self_r = (self.base_im[:, :, 0]).astype(np.int16)
        self_g = (self.base_im[:, :, 1]).astype(np.int16)
        self_b = (self.base_im[:, :, 2]).astype(np.int16)
        self_a = (self.base_im[:, :, 3]).astype(np.int16)
        diff = (end.r - start.r, \
            end.g - start.g, \
            end.b - start.b)

        transparency_r = np.zeros((self.height, self.width), dtype=np.float32) if diff[0] == 0 else ((self_r - start.r) / diff[0]).astype(np.float32)
        transparency_g = np.zeros((self.height, self.width), dtype=np.float32) if diff[1] == 0 else ((self_g - start.g) / diff[1]).astype(np.float32)
        transparency_b = np.zeros((self.height, self.width), dtype=np.float32) if diff[2] == 0 else ((self_b - start.b) / diff[2]).astype(np.float32)
        if not spill_compensation:
            transparency_r = np.clip(transparency_r.astype(np.float32), 0, 1)
            transparency_g = np.clip(transparency_g.astype(np.float32), 0, 1)
            transparency_b = np.clip(transparency_b.astype(np.float32), 0, 1)
      
        if (diff == (0, 0, 0)):
            raise ValueError(f"Invalid colors: {start}, {end}")
        transparency = (transparency_r + transparency_g + transparency_b) / \
            ((0 if diff[0] == 0 else 1) + \
            (0 if diff[1] == 0 else 1) + \
            (0 if diff[2] == 0 else 1))
        transparency = np.clip(transparency.astype(np.float32), 0, 1)

        new_a = (self_a - self_a * transparency).astype(np.uint8)
        mask = new_a == 0
        new_rgb = self.base_im[:, :, :3]
        new_rgb[mask] = (0, 0, 0)
        new_rgb = cast[npt.NDArray[np.uint8]](new_rgb)
        self.base_im[:, :, :3] = np.around(new_rgb)
        self.base_im[:, :, 3] = np.around(new_a)

        return self

    @check_writeable
    def draw_border(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        border: Border,
    ) -> Self:
        if border.width == 0:
            return self
        self.base_im = cv2.rectangle(
            self.base_im,
            (x, y),
            (x + width, y + height),
            border.color,
            border.width * 2,
            lineType=cv2.LINE_AA,
        )
        return self

    @check_writeable
    def resize(
        self,
        width: int = -1,
        height: int = -1,
        interpolation: Interpolation = Interpolation.BILINEAR,
    ) -> Self:
        """Resizes the image to the given width and height inplace.

        If only one of the dimensions is specified, the other dimension is
        calculated to preserve the aspect ratio.

        Args:
            width: The new width of the image.
                -1 to keep the original aspect ratio.
            height: The new height of the image.
                -1 to keep the original aspect ratio.
            interpolation: The interpolation method to use.

        Raises:
            ValueError: If both width and height are not specified.
        """
        if width < 0 and height < 0:
            raise ValueError("Either width or height must be specified")
        if width < 0:
            width = round(self.width * height / self.height)
        elif height < 0:
            height = round(self.height * width / self.width)

        flag = interpolation.value
        self.base_im = cv2.resize(
            self.base_im,
            (width, height),
            interpolation=flag,
        )
        return self

    @check_writeable
    def rescale(
        self,
        scale: float,
        interpolation: Interpolation = Interpolation.BILINEAR,
    ) -> Self:
        """Resizes the image by the given scale inplace.

        Args:
            scale: The scale to resize the image by.
            interpolation: The interpolation method to use.
        """
        return self.resize(
            width=round(self.width * scale),
            height=round(self.height * scale),
            interpolation=interpolation,
        )

    @check_writeable
    def thumbnail(
        self,
        max_width: int = -1,
        max_height: int = -1,
        interpolation: Interpolation = Interpolation.BILINEAR,
    ) -> Self:
        """Resizes the image to fit within the given dimensions inplace.

        If dimension is not specified, original dimension is used.

        Args:
            max_width: The maximum width of the image.
            max_height: The maximum height of the image.
            interpolation: The interpolation method to use.
        """
        if max_width < 0 and max_height < 0:
            return self
        if max_width < 0:
            max_width = self.width
        elif max_height < 0:
            max_height = self.height

        if self.width <= max_width and self.height <= max_height:
            return self

        scale = min(max_width / self.width, max_height / self.height)
        return self.rescale(scale, interpolation)

    def copy(self) -> Self:
        """Returns a copy of the image.

        Useful when the original image needs to be preserved.
        """
        return self.__class__(self.base_im.copy())

    @check_writeable
    def fill(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        color: Color = Palette.WHITE,
    ) -> Self:
        self.base_im[y:y + height, x:x + width] = color
        return self

    @check_writeable
    def mask(self, mask: ImageMask) -> Self:
        """Apply mask to image inplace.

        Alpha channel of the image will be multiplied by the mask.

        Args:
            mask: a 2D numpy array of shape (height, width) with values in [0, 255]
                or a boolean array of shape (height, width).

        Raises:
            ValueError: if mask size is not same as image size.
        """
        if mask.dtype == np.bool_:
            mask_ = mask.astype(np.uint8) * 255
            mask = cast[ImageMask](mask_)
        h, w = mask.shape
        if h != self.height or w != self.width:
            raise ValueError(f"Mask size must be same as image size: "
                             f"expected ({self.height}, {self.width}), "
                             f"got ({h}, {w})")
        indices = mask != 255
        coef = mask[indices] / 255.0
        self.base_im[indices, 3] = self.base_im[indices, 3] * coef
        return self

    @property
    def red(self) -> ImageMask:
        return cast[ImageMask](self.base_im[:, :, 0])

    @property
    def green(self) -> ImageMask:
        return cast[ImageMask](self.base_im[:, :, 1])

    @property
    def blue(self) -> ImageMask:
        return cast[ImageMask](self.base_im[:, :, 2])

    @property
    def alpha(self) -> ImageMask:
        return cast[ImageMask](self.base_im[:, :, 3])

    def save(self, path: PathLike) -> None:
        save_im = cv2.cvtColor(self.base_im, cv2.COLOR_RGBA2BGRA)
        if not cv2.imwrite(str(path), save_im):
            raise IOError(f"Cannnot save image to {path!r}")

    def show(self, lib: Literal["cv2", "PIL"] = "PIL") -> None:
        if lib == "PIL":
            show_im = PILImage.fromarray(self.base_im)
            show_im.show()
        else:
            show_im = cv2.cvtColor(self.base_im, cv2.COLOR_RGBA2BGR)
            cv2.imshow("image", show_im)
            cv2.waitKey(0)

    def to_pil(self) -> PILImage.Image:
        return PILImage.fromarray(self.base_im)

    def to_rgb(self) -> Self:
        im = cv2.cvtColor(self.base_im, cv2.COLOR_RGBA2RGB)
        return self.__class__.from_raw(im)

    def to_grayscale(self) -> Self:
        im = cv2.cvtColor(self.base_im, cv2.COLOR_RGBA2GRAY)
        return self.__class__.from_raw(im)

    def _repr_png_(self) -> bytes:
        """iPython display hook support"""
        im = self.to_pil()
        return im._repr_png_()  # type: ignore
