import sys

from .typing import *

if sys.version_info >= (3, 10):
    from bisect import bisect_left, bisect_right
else:
    from .bisect import bisect_left, bisect_right

__all__ = [
    "bisect_left",
    "bisect_right",
    "ImageMask",
    "PathLike",
    "Undefined",
    "undefined",
]
