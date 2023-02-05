from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Generic, TypeVar

import numpy as np
import numpy.typing as npt

ImageMask = npt.NDArray[np.uint8]
PathLike = str | Path

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


__all__ = ["ImageMask", "PathLike", "Undefined", "undefined", "cast"]
