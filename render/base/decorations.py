from abc import abstractmethod
from enum import Enum
from typing import Sequence
from typing_extensions import Self

from .image import RenderImage


class BoxSizing(Enum):
    CONTENT_BOX = 1
    BORDER_BOX = 2
    FULL_BOX = 3


class Decoration:
    pass


class ForegroundDecoration(Decoration):

    def __init__(self, box_sizing: BoxSizing) -> None:
        super(ForegroundDecoration, self).__init__()
        self.box_sizing = box_sizing

    @abstractmethod
    def apply(self, obj: RenderImage) -> RenderImage:
        raise NotImplementedError


class BackgroundDecoration(Decoration):

    @abstractmethod
    def apply(
        self,
        obj: RenderImage,
        bg: RenderImage,
        context: "render.base.RenderObject",
    ) -> RenderImage:
        raise NotImplementedError


class Decorations:

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
        context: "render.base.RenderObject",
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


import render  # for type hints
