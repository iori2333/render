from typing_extensions import Self, override

import cv2

from render.base import BoxSizing, InplaceDecoration, RenderImage


class Grayscale(InplaceDecoration):
    """Convert image to grayscale.
    
    Attributes:
        amount: Amount of grayscale (0.0 - 1.0).
        box_sizing: Box sizing to apply grayscale.
    """

    def __init__(
        self,
        amount: float,
        box_sizing: BoxSizing,
    ) -> None:
        super().__init__(box_sizing)
        self.amount = amount

    @classmethod
    def of(
        cls,
        amount: float = 1.0,
        box_sizing: BoxSizing = BoxSizing.CONTENT_BOX,
    ) -> Self:
        return cls(amount, box_sizing)

    @override
    def apply(self, im: RenderImage) -> RenderImage:
        amount = max(0, min(1, self.amount))
        im.base_im[..., :3] = cv2.addWeighted(
            im.base_im[..., :3],
            1 - amount,
            im.to_grayscale().base_im[..., :3],
            amount,
            0,
        )
        return im
