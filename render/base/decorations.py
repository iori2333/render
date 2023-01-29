from __future__ import annotations

from abc import abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Sequence
from typing_extensions import Self

from .image import RenderImage

if TYPE_CHECKING:
    from .object import RenderObject


class BoxSizing(Enum):
    CONTENT_BOX = 1
    BORDER_BOX = 2
    FULL_BOX = 3


class Decoration:
    pass


class ForegroundDecoration(Decoration):
    """Decorations that are applied on top of the content."""

    def __init__(self, box_sizing: BoxSizing) -> None:
        super(ForegroundDecoration, self).__init__()
        self.box_sizing = box_sizing

    @abstractmethod
    def apply(self, obj: RenderImage) -> RenderImage:
        """Apply foreground decoration

        Foreground decoration is applied on the top of given image. Depending on the
        box_sizing, the decoration is applied on the content layer or the full layer.

        Args:
            obj (RenderImage): image that the decoration is applied on

        Returns:
            RenderImage: rendered image
        """
        raise NotImplementedError()


class BackgroundDecoration(Decoration):
    """Decorations that are applied on the background."""

    @abstractmethod
    def apply(
        self,
        obj: RenderImage,
        bg: RenderImage,
        context: RenderObject,
    ) -> RenderImage:
        """Apply background decoration

        Background decoration is applied on the background layer of the rendering object.
        The `apply` method is called after the content is rendered and before the background
        is rendered. It changes the background layer of the rendering object using information
        from the content layer and context object.

        Args:
            obj (RenderImage): rendered foreground layer of rendering object
            bg (RenderImage): background layer in rendering
            context (RenderObject): The rendering object

        Returns:
            RenderImage: rendered image of background layer
        """
        raise NotImplementedError()


class Decorations:
    """Collection of decorations."""

    def __init__(self, decorations: Sequence[Decoration]) -> None:
        self._decorations = [
            d for d in decorations if isinstance(d, ForegroundDecoration)
        ]
        self._bg_decorations = [
            d for d in decorations if isinstance(d, BackgroundDecoration)
        ]

    @classmethod
    def of(cls, *decorations: Decoration) -> Self:
        return cls(decorations)

    def apply_content(self, obj: RenderImage) -> RenderImage:
        decorations = filter(lambda d: d.box_sizing == BoxSizing.CONTENT_BOX,
                             self._decorations)
        for decoration in decorations:
            obj = decoration.apply(obj)
        return obj

    def apply_full(self, obj: RenderImage) -> RenderImage:
        decorations = filter(lambda d: d.box_sizing == BoxSizing.FULL_BOX,
                             self._decorations)
        for decoration in decorations:
            obj = decoration.apply(obj)
        return obj

    def apply_background(
        self,
        obj: RenderImage,
        bg: RenderImage,
        context: RenderObject,
    ) -> RenderImage:
        for decoration in self._bg_decorations:
            bg = decoration.apply(obj, bg, context)
        return bg

    @property
    def has_bg_decorations(self) -> bool:
        return len(self._bg_decorations) > 0

    @property
    def decorations(self) -> Sequence[Decoration]:
        return [*self._decorations, *self._bg_decorations]
