from typing import Dict, List, Optional
from typing_extensions import Self, TypedDict, Unpack, override

from render.base import BaseStyle, RenderImage, RenderObject
from .utils import Box, DependencyGraph, LinearPolynomial


class Relative(TypedDict, total=False):
    above: RenderObject
    below: RenderObject
    left: RenderObject
    right: RenderObject
    align_top: RenderObject
    align_bottom: RenderObject
    align_left: RenderObject
    align_right: RenderObject
    center_vertical: RenderObject
    center_horizontal: RenderObject
    center: RenderObject


class RelativeContainer(RenderObject):

    def __init__(
        self,
        **kwargs: Unpack[BaseStyle],
    ) -> None:
        super(RelativeContainer, self).__init__(**kwargs)
        self.children: List[RenderObject] = []
        self.graph = DependencyGraph[RenderObject, str]().add_node(self)
        self.rendered_content: Optional[RenderImage] = None

    def add_child(
        self,
        child: RenderObject,
        **kwargs: Unpack[Relative],
    ) -> Self:
        if child in self.children:
            raise ValueError("Child already added")
        self.rendered_content = None
        self.children.append(child)
        for relation, target in kwargs.items():
            self.graph.add_edge(target, child, relation)  # type: ignore
        return self

    @property
    @override
    def content_width(self) -> int:
        if self.rendered_content is None:
            self.rendered_content = self.render_content()
        return self.rendered_content.width

    @property
    @override
    def content_height(self) -> int:
        if self.rendered_content is None:
            self.rendered_content = self.render_content()
        return self.rendered_content.height

    @override
    def render_content(self) -> RenderImage:
        if self.rendered_content is not None:
            return self.rendered_content
        if len(self.children) == 0:
            raise ValueError("No children to render")
        x = LinearPolynomial(x=1)
        y = LinearPolynomial(y=1)
        w = LinearPolynomial(w=1)
        h = LinearPolynomial(h=1)
        undef = LinearPolynomial(undef=1)
        boxes: Dict[RenderObject, Box] = {self: Box.of_size(x, y, w, h)}
        rendered: Dict[RenderObject, RenderImage] = {
            self: RenderImage.empty(1, 1)
        }
        topo = self.graph.topological_sort()
        for obj in topo:
            if obj is self:
                continue
            if obj not in rendered:
                rendered[obj] = obj.render()
            if obj not in boxes:
                # initialize x, y with undefined values
                boxes[obj] = Box.of_size(undef, undef, obj.width, obj.height)
            obj_box = boxes[obj]
            for pred in self.graph.get_predecessors(obj):
                for relative in self.graph.get_edges(pred, obj):
                    obj_box = obj_box.relative_to(boxes[pred], relative)
            if obj_box.x1 is undef or obj_box.y1 is undef:
                raise ValueError(f"Could not resolve position of object: "
                                 f"{obj}(x={obj_box.x1}, y={obj_box.y1})")
            boxes[obj] = obj_box
        del boxes[self]

        # TODO: Remove objects outside of container
        # e.g. A is align_left and align_top of container, B is left of A.
        #      If B not removed, A cannot meet the original requirement.
        x1 = [box.x1 for box in boxes.values()]
        y1 = [box.y1 for box in boxes.values()]
        x2 = [box.x2 for box in boxes.values()]
        y2 = [box.y2 for box in boxes.values()]
        x1_x = list(filter(lambda x: not x.contains_symbol("w"), x1))
        x1_w = list(filter(lambda x: x.contains_symbol("w"), x1))
        y1_y = list(filter(lambda x: not x.contains_symbol("h"), y1))
        y1_h = list(filter(lambda x: x.contains_symbol("h"), y1))
        x2_x = list(filter(lambda x: not x.contains_symbol("w"), x2))
        x2_w = list(filter(lambda x: x.contains_symbol("w"), x2))
        y2_y = list(filter(lambda x: not x.contains_symbol("h"), y2))
        y2_h = list(filter(lambda x: x.contains_symbol("h"), y2))
        min_x1 = min(x1_x or x1_w)
        min_y1 = min(y1_y or y1_h)
        max_x2 = max(x2_w or x2_x)
        max_y2 = max(y2_h or y2_y)
        width = max_x2 - min_x1
        height = max_y2 - min_y1
        if not width.is_const or not height.is_const:
            raise ValueError(
                f"Could not infer size of container: (w={width}, h={height})")
        x_eval = [
            x.eval(x=0, y=0, w=width.const, h=height.const) for x in x1 + x2
        ]
        y_eval = [
            y.eval(x=0, y=0, w=width.const, h=height.const) for y in y1 + y2
        ]
        x_offset = -min(x_eval) if min(x_eval) < 0 else 0
        y_offset = -min(y_eval) if min(y_eval) < 0 else 0
        im = RenderImage.empty(width=round(width.const + x_offset),
                               height=round(height.const + y_offset))
        for obj, box in boxes.items():
            x = box.x1.eval(x=x_offset,
                            y=y_offset,
                            w=width.const,
                            h=height.const)
            y = box.y1.eval(x=x_offset,
                            y=y_offset,
                            w=width.const,
                            h=height.const)
            im = im.paste(x=round(x), y=round(y), im=rendered[obj])
        self.rendered_content = im
        return im
