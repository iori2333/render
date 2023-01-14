from abc import ABC, abstractmethod
from typing import Generic, Iterable, Self, Sequence, TypeVar
from typing_extensions import override

import cv2
import numpy as np

from .properties import Alignment, Border, Direction
from .color import Color, Palette

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

    @abstractmethod
    def paste(self, im: Self, x: int, y: int) -> Self:
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
    def save(self, path: str) -> None:
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
            im.paste(child, x, y)
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
            im.paste(child, x, y)
            y += child.height
        return im


class CVImage(RawImage[cv2.Mat]):

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

    @override
    def paste(self, im: Self, x: int, y: int) -> Self:
        self.base_im[y:y + im.height, x:x + im.width, :] = im.base_im
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
        self.base_im = cv2.rectangle(
            self.base_im,
            (x, y),
            (x + width, y + height),
            border.color.as_tuple(),
            border.width,
            lineType=cv2.LINE_AA,
        )
        return self

    @override
    def save(self, path: str) -> None:
        cv2.imwrite(path, self.base_im)


RenderImage = CVImage
