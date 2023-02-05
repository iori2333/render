from __future__ import annotations

from abc import abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Sequence

from typing_extensions import Self

from .image import RenderImage
from .properties import BoundingBox

if TYPE_CHECKING:
    from .object import RenderObject


class DecoStage(Enum):
    INITIAL = "initial"
    AFTER_CONTENT = "after_content"
    BEFORE_PADDING = "before_padding"
    AFTER_PADDING = "after_padding"
    FINAL = "final"


class BoxSizing(Enum):
    CONTENT_BOX = 1
    BORDER_BOX = 2
    PADDING_BOX = 3
    FULL_BOX = 4


class Overlay(Enum):
    ABOVE_COMPOSITE = 1
    BELOW_COMPOSITE = 2
    ABOVE_OVERLAY = 3
    BELOW_OVERLAY = 4


class Decoration:
    pass


class InplaceDecoration(Decoration):
    """Decorations that directly modify the image."""

    def __init__(self, box_sizing: BoxSizing) -> None:
        super().__init__()
        self.box_sizing = box_sizing

    @abstractmethod
    def apply(self, im: RenderImage) -> RenderImage:
        """Apply inplace decoration.

        Args:
            im: image that the decoration is applied on.

        Returns:
            Modified image (Same size as the input image).
        """
        raise NotImplementedError()


class LayerDecoration(Decoration):
    """Decorations that render a layer to be overlaid on the render result."""

    def __init__(self, overlay: Overlay) -> None:
        super().__init__()
        self.overlay = overlay

    @abstractmethod
    def render_layer(self, im: RenderImage, obj: RenderObject) -> RenderImage:
        """Render a decoration layer depending on intermediate render result.

        Args:
            im: intermediate render result.
            obj: the decorated object.

        Returns:
            Decoration layer (Same size as the render result).
        """
        raise NotImplementedError()


class Decorations:
    """Collection of decorations."""

    def __init__(self, final_deco: Sequence[Decoration]) -> None:
        self._decorations: dict[DecoStage, list[Decoration]] = {
            DecoStage.INITIAL: [],
            DecoStage.AFTER_CONTENT: [],
            DecoStage.BEFORE_PADDING: [],
            DecoStage.AFTER_PADDING: [],
            DecoStage.FINAL: list(final_deco),
        }

    @classmethod
    def of(cls, *decorations: Decoration) -> Self:
        return cls(decorations)

    def initial(self, *decorations: Decoration) -> Self:
        self._decorations[DecoStage.INITIAL].extend(decorations)
        return self

    def after_content(self, *decorations: Decoration) -> Self:
        self._decorations[DecoStage.AFTER_CONTENT].extend(decorations)
        return self

    def before_padding(self, *decorations: Decoration) -> Self:
        self._decorations[DecoStage.BEFORE_PADDING].extend(decorations)
        return self

    def after_padding(self, *decorations: Decoration) -> Self:
        self._decorations[DecoStage.AFTER_PADDING].extend(decorations)
        return self

    def final(self, *decorations: Decoration) -> Self:
        self._decorations[DecoStage.FINAL].extend(decorations)
        return self

    @classmethod
    def apply(
        cls,
        im: RenderImage,
        obj: RenderObject,
        deco: Decoration,
    ) -> RenderImage:
        if isinstance(deco, InplaceDecoration):
            if deco.box_sizing == BoxSizing.CONTENT_BOX:
                box = obj.content_box
            elif deco.box_sizing == BoxSizing.BORDER_BOX:
                box = obj.border_box
            elif deco.box_sizing == BoxSizing.PADDING_BOX:
                box = obj.padding_box
            elif deco.box_sizing == BoxSizing.FULL_BOX:
                box = BoundingBox.of(0, 0, obj.width, obj.height)
            else:
                raise ValueError(f"Invalid box sizing {deco.box_sizing}")
            x, y, w, h = box
            cropped = RenderImage.from_raw(im.base_im[y:y + h, x:x + w])
            im = im.overlay(x, y, deco.apply(cropped))
        elif isinstance(deco, LayerDecoration):
            if deco.overlay == Overlay.ABOVE_COMPOSITE:
                im = im.paste(0, 0, deco.render_layer(im, obj))
            elif deco.overlay == Overlay.BELOW_COMPOSITE:
                im = deco.render_layer(im, obj).paste(0, 0, im)
            elif deco.overlay == Overlay.ABOVE_OVERLAY:
                im = im.overlay(0, 0, deco.render_layer(im, obj))
            elif deco.overlay == Overlay.BELOW_OVERLAY:
                im = deco.render_layer(im, obj).overlay(0, 0, im)
            else:
                raise ValueError(f"Invalid overlay {deco.overlay}")
        else:
            raise ValueError(f"Invalid decoration type {deco}")
        return im

    def apply_stage(self, im: RenderImage, obj: RenderObject,
                    stage: DecoStage) -> RenderImage:
        for decoration in self._decorations[stage]:
            im = self.apply(im, obj, decoration)
        return im

    def apply_initial(self, im: RenderImage, obj: RenderObject) -> RenderImage:
        return self.apply_stage(im, obj, DecoStage.INITIAL)

    def apply_after_content(
        self,
        im: RenderImage,
        obj: RenderObject,
    ) -> RenderImage:
        return self.apply_stage(im, obj, DecoStage.AFTER_CONTENT)

    def apply_after_padding(
        self,
        im: RenderImage,
        obj: RenderObject,
    ) -> RenderImage:
        return self.apply_stage(im, obj, DecoStage.AFTER_PADDING)

    def apply_final(
        self,
        im: RenderImage,
        obj: RenderObject,
    ) -> RenderImage:
        return self.apply_stage(im, obj, DecoStage.FINAL)

    def apply_before_padding(
        self,
        im: RenderImage,
        obj: RenderObject,
    ) -> RenderImage:
        return self.apply_stage(im, obj, DecoStage.BEFORE_PADDING)
