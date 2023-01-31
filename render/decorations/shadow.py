from __future__ import annotations

import cv2
import numpy as np
from typing_extensions import Self, override

from render.base import Color, LayerDecoration, RenderImage, RenderObject


class Shadow(LayerDecoration):

    def __init__(
        self,
        offset: tuple[int, int],
        blur_radius: int,
        color: Color,
    ) -> None:
        self.offset = offset
        self.blur_radius = blur_radius
        self.color = color

    def render_layer(self, im: RenderImage, obj: RenderObject) -> RenderImage:
        raise NotImplementedError()


class BoxShadow(Shadow):
    """Add shadow depending on the box model.

    Attributes:
        offset: Offset from the object box.
        blur_radius: Radius of gaussian blur.
        spread: Spread of shadow (px).
        color: Color of shadow.
    """

    def __init__(
        self,
        offset: tuple[int, int],
        blur_radius: int,
        spread: int,
        color: Color,
    ) -> None:
        super().__init__(offset, blur_radius, color)
        self.spread = spread

    @classmethod
    def of(
        cls,
        offset: tuple[int, int] = (0, 0),
        blur_radius: int = 0,
        spread: int = 0,
        color: Color = Color.of(0, 0, 0, 0.5),
    ) -> Self:
        blur_radius = max(0, blur_radius)
        if blur_radius > 0 and blur_radius % 2 == 0:
            blur_radius += 1  # in case of even number
        return cls(offset, blur_radius, spread, color)

    @override
    def render_layer(
        self,
        im: RenderImage,
        obj: RenderObject,
    ) -> RenderImage:
        layer = RenderImage.empty_like(im)
        spread = self.spread
        # calculate the size of the shadow
        width = (obj.content_width + obj.padding.width + obj.border.width * 2 +
                 spread * 2)
        height = (obj.content_height + obj.padding.height +
                  obj.border.width * 2 + spread * 2)
        # calculate the offset of the shadow
        x = self.offset[0] - spread + obj.margin.left
        y = self.offset[1] - spread + obj.margin.top
        # create the shadow
        layer = layer.overlay(x, y, RenderImage.empty(width, height,
                                                      self.color))
        if self.blur_radius > 0:
            layer.base_im = cv2.GaussianBlur(
                layer.base_im,
                (self.blur_radius, self.blur_radius),
                0,
            )
        return layer


class ContentShadow(Shadow):
    """Add shadow depending on the opacity of the content.

    Shadow opacity is calculated by multiplying the opacity of
    the content and the shadow color.

    Attributes:
        offset: Offset from the object box.
        blur_radius: Radius of gaussian blur.
        color: Color of shadow.
    """

    @classmethod
    def of(
        cls,
        offset: tuple[int, int] = (0, 0),
        blur_radius: int = 0,
        color: Color = Color.of(0, 0, 0, 0.5),
    ) -> Self:
        blur_radius = max(0, blur_radius)
        if blur_radius > 0 and blur_radius % 2 == 0:
            blur_radius += 1  # in case of even number
        return cls(offset, blur_radius, color)

    @override
    def render_layer(
        self,
        im: RenderImage,
        obj: RenderObject,
    ) -> RenderImage:
        content = obj.render_content()
        # generate the shadow
        shadow = RenderImage.empty_like(content, self.color)
        shadow_alpha = shadow.base_im[..., 3].astype(np.float32)
        content_alpha = content.base_im[..., 3].astype(np.float32) / 255
        shadow_alpha = (content_alpha * shadow_alpha).astype(np.uint8)
        shadow.base_im[..., 3] = shadow_alpha
        if self.blur_radius > 0:
            shadow.base_im = cv2.GaussianBlur(
                shadow.base_im,
                (self.blur_radius, self.blur_radius),
                0,
            )
        offset_x = (self.offset[0] + obj.margin.left + obj.border.width +
                    obj.padding.left)
        offset_y = (self.offset[1] + obj.margin.top + obj.border.width +
                    obj.padding.top)
        return RenderImage.empty_like(im).overlay(offset_x, offset_y, shadow)
