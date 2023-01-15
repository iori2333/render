from abc import abstractmethod
from enum import Enum
from typing_extensions import Self

from .image import RenderImage


class BoxSizing(Enum):
    CONTENT_BOX = 1
    BORDER_BOX = 2
    FULL_BOX = 3


class Decoration:

    def __init__(self, box_sizing: BoxSizing) -> None:
        self.box_sizing = box_sizing

    @classmethod
    def of(cls, box_sizing: BoxSizing = BoxSizing.CONTENT_BOX) -> Self:
        return cls(box_sizing)

    @abstractmethod
    def apply(self, obj: RenderImage) -> RenderImage:
        raise NotImplementedError


class Decorations(list[Decoration]):

    @classmethod
    def of(cls, *decorations: Decoration) -> Self:
        return cls(decorations)

    def apply(self, obj: RenderImage) -> RenderImage:
        for decoration in self:
            obj = decoration.apply(obj)
        return obj

    def apply_content(self, obj: RenderImage) -> RenderImage:
        decorations = filter(lambda d: d.box_sizing == BoxSizing.CONTENT_BOX,
                             self)
        for decoration in decorations:
            obj = decoration.apply(obj)
        return obj

    def apply_full(self, obj: RenderImage) -> RenderImage:
        decorations = filter(lambda d: d.box_sizing == BoxSizing.FULL_BOX,
                             self)
        for decoration in decorations:
            obj = decoration.apply(obj)
        return obj
