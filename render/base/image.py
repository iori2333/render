from typing import Iterable, Sequence
from typing_extensions import Self

import cv2
import numpy as np
import PIL.Image as PILImage

from render.utils import ImageMask, PathLike
from .color import Color, Palette
from .properties import Alignment, Border, Direction, Interpolation


class RenderImage:

    def __init__(self, base_im: cv2.Mat) -> None:
        self.base_im = base_im

    @classmethod
    def from_file(cls, path: PathLike) -> Self:
        im = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
        if im is None:
            raise IOError(f"Invalid image path: {path}")
        height, width, channels = im.shape
        if channels == 3:
            alpha = np.full((height, width, 1), 255, dtype=np.uint8)
            im = np.concatenate((im, alpha), axis=2)
        elif channels == 4:
            pass
        else:
            raise ValueError(f"Invalid color mode: {channels}")
        im = cv2.cvtColor(im, cv2.COLOR_BGRA2RGBA)
        return cls(im)

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
    def from_raw(cls, im: cv2.Mat) -> Self:
        height, width, channels = im.shape
        if channels == 3:
            alpha = np.full((height, width, 1), 255, dtype=np.uint8)
            im = np.concatenate((im, alpha), axis=2)
        elif channels == 4:
            pass
        else:
            raise ValueError(f"Invalid color mode: {channels}")
        return cls(im)

    @classmethod
    def concat(
        cls,
        images: Iterable[Self],
        direction: Direction,
        alignment: Alignment,
        color: Color = Palette.WHITE,
        spacing: int = 0,
    ) -> Self:
        images = list(images)
        if direction == Direction.HORIZONTAL:
            return cls.concat_horizontal(images, alignment, color, spacing)
        else:
            return cls.concat_vertical(images, alignment, color, spacing)

    @classmethod
    def concat_horizontal(
        cls,
        images: Sequence[Self],
        alignment: Alignment,
        color: Color = Palette.WHITE,
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
        color: Color = Palette.WHITE,
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

    def paste(self, x: int, y: int, im: Self) -> Self:
        im_self = PILImage.fromarray(self.base_im)
        im_paste = PILImage.fromarray(im.base_im)
        im_self.alpha_composite(im_paste, (x, y))
        self.base_im = np.array(im_self)
        return self

    def cover(self, x: int, y: int, im: Self) -> Self:
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

    def set_transparency(
        self,
        start: Color = Palette.WHITE,
        end: Color = Palette.BLACK,
        spill_compensation: bool = False,
    ) -> Self:
        self_r = np.array(self.base_im[:, :, 0]).astype(np.int16)
        self_g = np.array(self.base_im[:, :, 1]).astype(np.int16)
        self_b = np.array(self.base_im[:, :, 2]).astype(np.int16)
        self_a = np.array(self.base_im[:, :, 3]).astype(np.int16)
        diff = (end.r - start.r, \
            end.g - start.g, \
            end.b - start.b)

        transparency_r = np.zeros(
            (self.height,
             self.width), dtype=np.int16) if diff[0] == 0 else np.array(
                 (self_r - start.r) / diff[0]).astype(np.int16)
        transparency_g = np.zeros(
            (self.height,
             self.width), dtype=np.int16) if diff[1] == 0 else np.array(
                 (self_g - start.g) / diff[1]).astype(np.int16)
        transparency_b = np.zeros(
            (self.height,
             self.width), dtype=np.int16) if diff[2] == 0 else np.array(
                 (self_b - start.b) / diff[2]).astype(np.int16)
        if not spill_compensation:
            transparency_r = np.clip(
                np.array(transparency_r).astype(np.int16), 0, 1)
            transparency_g = np.clip(
                np.array(transparency_g).astype(np.int16), 0, 1)
            transparency_b = np.clip(
                np.array(transparency_b).astype(np.int16), 0, 1)

        if (diff == (0, 0, 0)):
            raise ValueError(f"Invalid colors: {start}, {end}")
        transparency = (transparency_r + transparency_g + transparency_b) / \
            ((0 if diff[0] == 0 else 1) + \
            (0 if diff[1] == 0 else 1) + \
            (0 if diff[2] == 0 else 1))
        transparency = np.clip(np.array(transparency).astype(np.int16), 0, 1)

        new_a = np.array(self_a - self_a * transparency).astype(np.uint8)
        mask = new_a == 0
        new_rgb = self.base_im[:, :, :3]
        new_rgb[mask] = (0, 0, 0)

        self.base_im[:, :, :3] = np.around(new_rgb)
        self.base_im[:, :, 3] = np.around(new_a)

        return self

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

    def resize(
        self,
        width: int = -1,
        height: int = -1,
        interpolation: Interpolation = Interpolation.BILINEAR,
    ) -> Self:
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

    def mask(self, mask: ImageMask) -> Self:
        h, w = mask.shape
        if h != self.height or w != self.width:
            raise ValueError("Mask size must be same as image size")
        indices = mask != 255
        coef = mask[indices] / 255.0
        self.base_im[indices, 3] = self.base_im[indices, 3] * coef
        return self

    def save(self, path: PathLike) -> None:
        save_im = cv2.cvtColor(self.base_im, cv2.COLOR_RGBA2BGRA)
        if not cv2.imwrite(str(path), save_im):
            raise IOError(f"Failed to save image to {path}")

    def show(self) -> None:
        show_im = cv2.cvtColor(self.base_im, cv2.COLOR_RGBA2BGR)
        cv2.imshow("image", show_im)
        cv2.waitKey(0)

    def to_rgb(self) -> Self:
        im = cv2.cvtColor(self.base_im, cv2.COLOR_RGBA2RGB)
        return self.__class__.from_raw(im)
