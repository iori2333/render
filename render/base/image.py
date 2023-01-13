from typing import Iterable, Self, Sequence

import cv2
import numpy as np

from .properties import Alignment, Direction
from .color import Color, ColorMode, Palette

BaseImage = cv2.Mat


class RenderImage:

    def __init__(
        self,
        width: int,
        height: int,
        color_mode: ColorMode,
        base_im: BaseImage,
    ) -> None:
        self.width = width
        self.height = height
        self.color_mode = color_mode
        self.base_im = base_im

    @classmethod
    def from_file(cls, path: str) -> Self:
        im = cv2.imread(path)
        if im is None:
            raise ValueError(f"Invalid image path: {path}")
        height, width, channels = im.shape
        if channels == 3:
            color_mode = ColorMode.RGB
        elif channels == 4:
            color_mode = ColorMode.RGBA
        else:
            raise ValueError(f"Invalid color mode: {channels}")
        return cls(width, height, color_mode, im)

    @classmethod
    def empty(
        cls,
        width: int,
        height: int,
        color_mode: ColorMode = ColorMode.RGBA,
        color: Color = Palette.WHITE,
    ) -> Self:
        if color_mode == ColorMode.RGB:
            im = np.zeros((height, width, 3), dtype=np.uint8)
            im[:] = color.to_rgb()
        elif color_mode == ColorMode.RGBA:
            im = np.zeros((height, width, 4), dtype=np.uint8)
            im[:] = color.to_rgba()
        else:
            raise ValueError(f"Invalid color mode: {color_mode}")

        return cls(width, height, color_mode, im)

    @classmethod
    def concat(
        cls,
        images: Iterable[Self],
        direction: Direction,
        alignment: Alignment,
    ):
        if direction == Direction.HORIZONTAL:
            return cls.concat_horizontal(list(images), alignment)
        return cls.concat_vertical(list(images), alignment)

    @classmethod
    def concat_horizontal(cls, images: Sequence[Self], alignment: Alignment):
        width = sum(im.width for im in images)
        height = max(im.height for im in images)
        color_mode = images[0].color_mode
        im = cls.empty(width, height, color_mode)
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
    def concat_vertical(cls, images: Sequence[Self], alignment: Alignment):
        width = max(im.width for im in images)
        height = sum(im.height for im in images)
        color_mode = images[0].color_mode
        im = cls.empty(width, height, color_mode)
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

    def paste(self, im: Self, x: int, y: int) -> Self:
        self.base_im[y:y + im.height, x:x + im.width, :] = im.base_im
        return self

    def draw_border(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        color: Color,
        thickness: int,
    ) -> Self:
        self.base_im = cv2.rectangle(
            self.base_im,
            (x, y),
            (x + width, y + height),
            color.to_rgba(),
            thickness,
            lineType=cv2.LINE_AA,
        )
        return self

    def save(self, path: str) -> None:
        cv2.imwrite(path, self.base_im)