import sys

if sys.version_info >= (3, 10):
    from bisect import bisect_left, bisect_right
else:
    from .bisect import bisect_left, bisect_right

from .typing import *

__all__ = [
    "bisect_left",
    "bisect_right",
    "ImageMask",
    "PathLike",
    "Undefined",
    "undefined",
]
