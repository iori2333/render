from abc import ABC, abstractmethod
from typing import Generic, Iterable, Sequence, TypeVar
from typing_extensions import override, Self

import cv2
import numpy as np
import PIL.Image as PILImage

from .properties import Alignment, Border, Direction, Interpolation
from .color import Color, Palette

ImageMask = np.ndarray[int, np.dtype[np.uint8]]
T = TypeVar("T")


class RawImage(ABC, Generic[T]):

    def __init__(self, base_im: T) -> None:
        self.base_im = base_im

    @property
    @abstractmethod
    def width(self) -> int:
        raise NotImplementedError()

    @property
    @abstractmethod
    def height(self) -> int:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def from_file(cls, path: str) -> Self:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def empty(
        cls,
        width: int,
        height: int,
        color: Color = Palette.WHITE,
    ) -> Self:
        raise NotImplementedError()

    @classmethod
    def empty_like(cls, im: Self, color: Color = Palette.WHITE) -> Self:
        return cls.empty(im.width, im.height, color)

    @classmethod
    @abstractmethod
    def from_raw(cls, im: T) -> Self:
        raise NotImplementedError()

    @abstractmethod
    def paste(self, x: int, y: int, im: Self) -> Self:
        raise NotImplementedError()

    @abstractmethod
    def cover(self, x: int, y: int, im: Self) -> Self:
        raise NotImplementedError()

    @abstractmethod
    def set_transparent(self,
        color_transparent_0: Color = Color.of(255, 255, 255),
        color_transparent_100: Color = Color.of(0, 0, 0),
        spill_compensation: bool = False
        ) -> Self:
        raise NotImplementedError()

    @abstractmethod
    def draw_border(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        border: Border,
    ) -> Self:
        raise NotImplementedError()

    @abstractmethod
    def resize(
        self,
        width: int = -1,
        height: int = -1,
        interpolation: Interpolation = Interpolation.BILINEAR,
    ) -> Self:
        raise NotImplementedError()

    @abstractmethod
    def fill(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        color: Color,
    ) -> Self:
        raise NotImplementedError()

    @abstractmethod
    def mask(self, mask: ImageMask) -> Self:
        raise NotImplementedError()

    @abstractmethod
    def save(self, path: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def show(self) -> None:
        raise NotImplementedError()

    @classmethod
    def concat(
        cls,
        images: Iterable[Self],
        direction: Direction,
        alignment: Alignment,
        color: Color = Palette.WHITE,
    ) -> Self:
        images = list(images)
        if direction == Direction.HORIZONTAL:
            return cls.concat_horizontal(images, alignment, color)
        else:
            return cls.concat_vertical(images, alignment, color)

    @classmethod
    def concat_horizontal(
        cls,
        images: Sequence[Self],
        alignment: Alignment,
        color: Color = Palette.WHITE,
    ) -> Self:
        width = sum(im.width for im in images)
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
            x += child.width
        return im

    @classmethod
    def concat_vertical(
        cls,
        images: Sequence[Self],
        alignment: Alignment,
        color: Color = Palette.WHITE,
    ) -> Self:
        width = max(im.width for im in images)
        height = sum(im.height for im in images)
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
            y += child.height
        return im


class RenderImage(RawImage[cv2.Mat]):

    @classmethod
    @override
    def from_file(cls, path: str) -> Self:
        im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if im is None:
            raise ValueError(f"Invalid image path: {path}")
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
    @override
    def empty(
        cls,
        width: int,
        height: int,
        color: Color = Palette.WHITE,
    ) -> Self:
        im = np.zeros((height, width, 4), dtype=np.uint8)
        im[:] = color
        return cls(im)

    @classmethod
    @override
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

    @property
    @override
    def width(self) -> int:
        return self.base_im.shape[1]
    
    @property
    @override
    def height(self) -> int:
        return self.base_im.shape[0]

    @override
    def paste(self, x: int, y: int, im: Self) -> Self:
        im_self = PILImage.fromarray(self.base_im)
        im_paste = PILImage.fromarray(im.base_im)
        im_self.alpha_composite(im_paste, (x, y))
        self.base_im = np.array(im_self)
        return self

    @override
    def cover(self, x: int, y: int, im: Self) -> Self:
        b, t, l, r = (y, y + im.height, x, x + im.width)
        cover_rgb = im.base_im[:, :, :3]
        self_rgb = self.base_im[b:t, l:r, :3]
        cover_a = np.expand_dims(im.base_im[:, :, 3], 2)
        self_a = np.expand_dims(self.base_im[b:t, l:r, 3], 2)

        mask = (cover_a == 0).squeeze(-1)

        new_rgb = cover_rgb
        new_rgb[mask] = self_rgb[mask]

        new_a = cover_a
        new_a[mask] = self_a[mask]

        self.base_im[b:t, l:r, :3] = np.around(new_rgb).astype(np.uint8)
        self.base_im[b:t, l:r, 3] = np.around(new_a).astype(np.uint8).squeeze(2)

        return self

    @override
    def set_transparent(self,
        color_transparent_0: Color = Color.of(255, 255, 255),
        color_transparent_100: Color = Color.of(0, 0, 0),
        spill_compensation: bool = False
        ) -> Self:
        self_r = np.array(self.base_im[:, :, 0]).astype(np.int16)
        self_g = np.array(self.base_im[:, :, 1]).astype(np.int16)
        self_b = np.array(self.base_im[:, :, 2]).astype(np.int16)
        self_a = np.array(self.base_im[:, :, 3]).astype(np.int16)
        transparent_diff = (color_transparent_100.r - color_transparent_0.r, \
            color_transparent_100.g - color_transparent_0.g, \
            color_transparent_100.b - color_transparent_0.b)

        transparent_r = np.zeros((self.height, self.width), dtype=np.int16) if transparent_diff[0] == 0 else np.array((self_r - color_transparent_0.r) / transparent_diff[0]).astype(np.int16)
        transparent_g = np.zeros((self.height, self.width), dtype=np.int16) if transparent_diff[1] == 0 else np.array((self_g - color_transparent_0.g) / transparent_diff[1]).astype(np.int16)
        transparent_b = np.zeros((self.height, self.width), dtype=np.int16) if transparent_diff[2] == 0 else np.array((self_b - color_transparent_0.b) / transparent_diff[2]).astype(np.int16)
        if not spill_compensation:
            transparent_r = np.clip(np.array(transparent_r).astype(np.int16), 0, 1)
            transparent_g = np.clip(np.array(transparent_g).astype(np.int16), 0, 1)
            transparent_b = np.clip(np.array(transparent_b).astype(np.int16), 0, 1)
      
        if (transparent_diff == (0, 0, 0)):
            raise ValueError(f"Invalid colors: {color_transparent_0}, {color_transparent_100}")
        transparent = (transparent_r + transparent_g + transparent_b) / \
            ((0 if transparent_diff[0] == 0 else 1) + \
            (0 if transparent_diff[1] == 0 else 1) + \
            (0 if transparent_diff[2] == 0 else 1))
        transparent = np.clip(np.array(transparent).astype(np.int16), 0, 1)

        new_a = np.array(self_a - self_a * transparent).astype(np.uint8)
        mask = new_a == 0
        new_rgb = self.base_im[:, :, :3]
        new_rgb[mask] = (0, 0, 0)

        self.base_im[:, :, :3] = np.around(new_rgb).astype(np.uint8)
        self.base_im[:, :, 3] = np.around(new_a).astype(np.uint8)

        return self

    @override
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

    @override
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

    @override
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

    @override
    def mask(self, mask: ImageMask) -> Self:
        h, w = mask.shape
        if h != self.height or w != self.width:
            raise ValueError("Mask size must be same as image size")
        indices = mask != 255
        coef = mask[indices] / 255.0
        self.base_im[indices, 3] = self.base_im[indices, 3] * coef
        return self

    @override
    def save(self, path: str) -> None:
        save_im = cv2.cvtColor(self.base_im, cv2.COLOR_RGBA2BGRA)
        cv2.imwrite(path, save_im)

    @override
    def show(self) -> None:
        show_im = cv2.cvtColor(self.base_im, cv2.COLOR_RGBA2BGR)
        cv2.imshow("image", show_im)
        cv2.waitKey(0)
