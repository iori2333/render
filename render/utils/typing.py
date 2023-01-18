import sys
from pathlib import Path
from typing import Union

import numpy as np

if sys.version_info >= (3, 9):
    ImageMask = np.ndarray[int, np.dtype[np.uint8]]
else:
    ImageMask = np.ndarray

PathLike = Union[str, Path]

__all__ = ["ImageMask", "PathLike"]
