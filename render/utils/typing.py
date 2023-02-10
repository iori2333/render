from __future__ import annotations

from pathlib import Path
from typing import Any, Generic, TypeVar, Union

import numpy as np
import numpy.typing as npt

ImageMask = Union[npt.NDArray[np.uint8], npt.NDArray[np.bool_]]
PathLike = Union[str, Path]

T = TypeVar("T")


class Undefined:

    _inst = None

    def __new__(cls) -> Undefined:
        if cls._inst is None:
            cls._inst = super().__new__(cls)
        return cls._inst

    @classmethod
    def __repr__(cls) -> str:
        return "Undefined"

    @classmethod
    def default(cls, value: Any, default: T) -> T:
        if value is undefined:
            return default
        return value


undefined = Undefined()


class cast(Generic[T]):

    def __new__(cls, value: Any) -> T:
        return value


__all__ = [
    "ImageMask",
    "PathLike",
    "Undefined",
    "cast",
    "undefined",
]
