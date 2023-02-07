from __future__ import annotations

from typing import Iterable

from typing_extensions import Literal, Self, Unpack, override

from render.base import (Alignment, BaseStyle, RenderImage, RenderObject,
                         cached, volatile)


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
