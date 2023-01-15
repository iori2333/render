from abc import ABC, abstractmethod
from typing import Generic, Iterable, Sequence, TypeVar
from typing_extensions import override, Self

import cv2
import numpy as np

from .properties import Alignment, Border, Direction, Interpolation
from .color import Color, Palette

ImageMask = np.ndarray[int, np.dtype[np.uint8]]
T = TypeVar("T")


class RawImage(ABC, Generic[T]):

    def __init__(self, width: int, height: int, base_im: T) -> None:
        self.width = width
        self.height = height
        self.base_im = base_im

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
        return cls(width, height, im)

    @classmethod
    @override
    def empty(
        cls,
        width: int,
        height: int,
        color: Color = Palette.WHITE,
    ) -> Self:
        im = np.zeros((height, width, 4), dtype=np.uint8)
        im[:] = color.as_tuple()
        return cls(width, height, im)

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
        return cls(width, height, im)

    @override
    def paste(self, x: int, y: int, im: Self) -> Self:
        b, t, l, r = (y, y + im.height, x, x + im.width)
        paste_rgb = im.base_im[:, :, :3]
        self_rgb = self.base_im[b:t, l:r, :3]
        paste_a = np.expand_dims(im.base_im[:, :, 3], 2)
        self_a = np.expand_dims(self.base_im[b:t, l:r, 3], 2)

        mask = (self_a == 0).squeeze(-1)
        alpha = paste_a / 255.0  # type: ignore
        new_a = paste_a + self_a * (1 - alpha)
        new_a[mask] = 1

        coef = paste_a / new_a
        new_rgb = paste_rgb * coef + self_rgb * (1 - coef)

        new_rgb[mask] = paste_rgb[mask]
        new_a[mask] = paste_a[mask]

        self.base_im[b:t, l:r, :3] = np.around(new_rgb).astype(np.uint8)
        self.base_im[b:t, l:r, 3] = np.around(new_a).astype(np.uint8).squeeze(2)

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
            border.color.as_tuple(),
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
        self.width = width
        self.height = height
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
        self.base_im[y:y + height, x:x + width] = color.as_tuple()
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
