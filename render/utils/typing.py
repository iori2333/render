from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Union, TypeVar

import numpy as np

if sys.version_info >= (3, 9):
    ImageMask = np.ndarray[int, np.dtype[np.uint8]]
else:
    ImageMask = np.ndarray

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

__all__ = ["ImageMask", "PathLike", "Undefined", "undefined"]
