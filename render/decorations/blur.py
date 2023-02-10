import cv2
from typing_extensions import Self, override

from render.base import BoxSizing, InplaceDecoration, RenderImage


class GaussianBlur(InplaceDecoration):

    def __init__(
        self,
        blur_radius: int,
        box_sizing: BoxSizing,
    ) -> None:
        super().__init__(box_sizing)
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
    def apply(self, im: RenderImage) -> RenderImage:
        im.base_im = cv2.GaussianBlur(
            im.base_im,
            (self.blur_radius, self.blur_radius),
            0,
        )
        return im
