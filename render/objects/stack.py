from __future__ import annotations

from typing import Iterable

from copy import deepcopy
import cv2
import numpy as np
from sys import getrefcount
from typing_extensions import Literal, Self, Unpack, override

from render.base import (Alignment, BaseStyle, Palette,
                         RenderImage, RenderObject, cached, volatile)


class Stack(RenderObject):
    """A container that stacks its children on top of each other.

    The first child is at the bottom, the last child is at the top.
    And the final content size is the size of the largest child.

    Attributes:
        children: list of children to be stacked.
        vertical_alignment: alignment of children in vertical direction.
        horizontal_alignment: alignment of children in horizontal direction.
        paste_mode: paste mode of children. See RenderImage.paste.
    """

    def __init__(
        self,
        children: Iterable[RenderObject],
        vertical_alignment: Alignment,
        horizontal_alignment: Alignment,
        paste_mode: Literal["paste", "overlay", "cover"],
        **kwargs: Unpack[BaseStyle],
    ) -> None:
        super().__init__(**kwargs)
        with volatile(self) as vlt:
            self.children = vlt.list(children)
            self.vertical_alignment = vertical_alignment
            self.horizontal_alignment = horizontal_alignment
            self.paste_mode = paste_mode

    @classmethod
    def from_children(
        cls,
        children: Iterable[RenderObject],  # bottom to top
        alignment: Alignment = Alignment.START,
        vertical_alignment: Alignment | None = None,
        horizontal_alignment: Alignment | None = None,
        paste_mode: Literal["paste", "overlay", "cover"] = "paste",
        **kwargs: Unpack[BaseStyle],
    ) -> Self:
        if vertical_alignment is None:
            vertical_alignment = alignment
        if horizontal_alignment is None:
            horizontal_alignment = alignment
        return cls(children, vertical_alignment, horizontal_alignment,
                   paste_mode, **kwargs)

    @property
    @cached
    @override
    def content_width(self) -> int:
        return max(child.width
                   for child in self.children) if self.children else 0

    @property
    @cached
    @override
    def content_height(self) -> int:
        return max(child.height
                   for child in self.children) if self.children else 0

    @cached
    @override
    def render_content(self) -> RenderImage:
        rendered = map(lambda child: child.render(), self.children)
        im = RenderImage.empty(self.width, self.height)
        for child in rendered:
            if self.vertical_alignment == Alignment.START:
                y = 0
            elif self.vertical_alignment == Alignment.CENTER:
                y = (self.height - child.height) // 2
            else:
                y = self.height - child.height

            if self.horizontal_alignment == Alignment.START:
                x = 0
            elif self.horizontal_alignment == Alignment.CENTER:
                x = (self.width - child.width) // 2
            else:
                x = self.width - child.width

            if self.paste_mode == "paste":
                im = im.paste(x, y, child)
            elif self.paste_mode == "overlay":
                im = im.overlay(x, y, child)
            elif self.paste_mode == "cover":
                im = im.cover(x, y, child)
            else:
                raise ValueError(f"Invalid paste mode: {self.paste_mode}")
        return im

    @classmethod
    def list_leaves(cls, root_node: RenderObject, depth: int) -> list[list[int, RenderObject, list[RenderObject]]]:
        if root_node.tree_nodes == []:
            return [[depth, root_node, [root_node]]]
        leaves_list = []
        for c in root_node.tree_nodes:
            leaves_list += cls.list_leaves(c, depth + 1)
        for leaf in leaves_list:
            leaf[2].append(root_node)
        return leaves_list
    
    def render_tree_preparation(self, depth: int, offset: tuple[int, int]) -> bool:
        self.tree_nodes = []
        self.offset_from_origin = offset
        if not self.children:
            self.depth = depth
            return True
        # if getrefcount(self.children) > 2:
        #     self.children = deepcopy(self.children)
        depth_accumulation = 0
        max_height = max(map(lambda child: child.height, self.children))
        max_width = max(map(lambda child: child.width, self.children))
        for child in reversed(self.children):
            if self.horizontal_alignment == Alignment.START:
                offset_h = 0
            elif self.horizontal_alignment == Alignment.END:
                offset_h = max_width - child.width
            else:
                offset_h = int((max_width - child.width) / 2)
            if self.vertical_alignment == Alignment.START:
                offset_v = 0
            elif self.vertical_alignment == Alignment.END:
                offset_v = max_height - child.height
            else:
                offset_v = int((max_height - child.height) / 2)
            compress = child.render_tree_preparation(depth, (offset[0] + offset_h, offset[1] + offset_v))
            if compress:
                child.depth += 1
            child.depth += depth_accumulation
            depth_accumulation = child.depth
            self.tree_nodes.append(child)
        self.depth = depth_accumulation + 1
        return False

    def render_self(self) -> cv2.Mat:
        im = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        im[:] = Palette.TRANSPARENT
        return im
