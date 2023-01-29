from typing_extensions import Self, override

import cv2

from render.base import BoxSizing, ForegroundDecoration, RenderImage


class GaussianBlur(ForegroundDecoration):

    def __init__(
        self,
        blur_radius: int,
        box_sizing: BoxSizing,
    ) -> None:
        super(GaussianBlur, self).__init__(box_sizing)
        self.blur_radius = blur_radius

    @classmethod
    def of(
        cls,
        blur_radius: int = 21,
        box_sizing: BoxSizing = BoxSizing.CONTENT_BOX,
    ) -> Self:
        if blur_radius % 2 == 0:
            blur_radius += 1  # in case of even number
        return cls(blur_radius, box_sizing)

    @override
    def apply(self, obj: RenderImage) -> RenderImage:
        obj.base_im = cv2.GaussianBlur(
            obj.base_im,
            (self.blur_radius, self.blur_radius),
            0,
        )
        return obj
