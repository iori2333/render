import sys

if sys.version_info >= (3, 10):
    import bisect as pybisect
    find_leftmost = pybisect.bisect_left
    find_rightmost = pybisect.bisect_right
else:
    from .bisect import find_leftmost, find_rightmost

__all__ = [
    "find_leftmost",
    "find_rightmost",
]
