from abc import abstractmethod
from typing import Optional
from typing_extensions import override

import numpy as np
import cv2

from render.base import Decoration, RenderImage, ImageMask, BoxSizing


class Crop(Decoration):

    @abstractmethod
    def get_mask(self, obj: RenderImage) -> ImageMask:
        raise NotImplementedError()

    @override
    def apply(self, obj: RenderImage) -> RenderImage:
        mask = self.get_mask(obj)
        obj = obj.mask(mask)
        return obj


class RoundedCrop(Crop):

    def __init__(
        self,
        radius: Optional[int],
        box_sizing: BoxSizing,
    ) -> None:
        super(RoundedCrop, self).__init__(box_sizing)
        self.radius = radius

    @classmethod
    def of(
        cls,
        radius: Optional[int] = None,
        box_sizing: BoxSizing = BoxSizing.CONTENT_BOX,
    ) -> "RoundedCrop":
        return cls(radius, box_sizing)

    @override
    def get_mask(self, obj: RenderImage) -> ImageMask:
        if self.radius is None:
            radius = min(obj.height, obj.width) // 2
        else:
            radius = self.radius

        mask = np.zeros((obj.height, obj.width), dtype=np.uint8)
        mask = cv2.circle(
            mask,
            (obj.height // 2, obj.width // 2),
            radius,
            255,
            thickness=-1,
            lineType=cv2.LINE_AA,
        )
        return mask


class RectCrop(Crop):

    def __init__(
        self,
        width: Optional[int],
        height: Optional[int],
        border_radius: int,
        box_sizing: BoxSizing,
    ) -> None:
        super(RectCrop, self).__init__(box_sizing)
        self.width = width
        self.height = height
        self.border_radius = border_radius

    @classmethod
    def of(
        cls,
        width: Optional[int] = None,
        height: Optional[int] = None,
        border_radius: int = 0,
        box_sizing: BoxSizing = BoxSizing.CONTENT_BOX,
    ) -> "RectCrop":
        return cls(width, height, border_radius, box_sizing)

    @classmethod
    def of_square(
        cls,
        size: Optional[int] = None,
        border_radius: int = 0,
        box_sizing: BoxSizing = BoxSizing.CONTENT_BOX,
    ) -> "RectCrop":
        return cls(size, size, border_radius, box_sizing)

    @override
    def get_mask(self, obj: RenderImage) -> ImageMask:
        height = self.height if self.height is not None else obj.height
        width = self.width if self.width is not None else obj.width
        start_x = (obj.width - width) // 2
        start_y = (obj.height - height) // 2
        mask = np.zeros((obj.height, obj.width), dtype=np.uint8)
        if self.border_radius == 0:
            return cv2.rectangle(
                mask,
                (start_x, start_y),
                (start_x + width, start_y + height),
                255,
                thickness=-1,
                lineType=cv2.LINE_AA,
            )

        if self.border_radius > min(width, height) // 2:
            self.border_radius = min(width, height) // 2

        corners = [
            (start_x + self.border_radius, start_y + self.border_radius),
            (start_x + self.border_radius,
             start_y + height - self.border_radius),
            (start_x + width - self.border_radius,
             start_y + self.border_radius),
            (start_x + width - self.border_radius,
             start_y + height - self.border_radius),
        ]
        for corner in corners:
            mask = cv2.circle(
                mask,
                corner,
                self.border_radius,
                255,
                thickness=-1,
                lineType=cv2.LINE_AA,
            )
        mask = cv2.rectangle(
            mask,
            (start_x, start_y + self.border_radius),
            (start_x + width, start_y + height - self.border_radius),
            255,
            thickness=-1,
            lineType=cv2.LINE_AA,
        )
        mask = cv2.rectangle(
            mask,
            (start_x + self.border_radius, start_y),
            (start_x + width - self.border_radius, start_y + height),
            255,
            thickness=-1,
            lineType=cv2.LINE_AA,
        )
        return mask
