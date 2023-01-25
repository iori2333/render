from __future__ import annotations

from typing import Tuple
from typing_extensions import Self, TypedDict, Unpack, override

from render.base import BaseStyle, RenderImage, RenderObject
from .utils import Box, DependencyGraph, LinearPolynomial, partition

XY = Tuple[int, int]
ConstraintTuple = Tuple[RenderObject, str, RenderObject]


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
    prior_to: RenderObject


class Constraint(TypedDict, total=False):
    above: RenderObject
    below: RenderObject
    left: RenderObject
    right: RenderObject


class RelativeContainer(RenderObject):

    def __init__(
        self,
        **kwargs: Unpack[BaseStyle],
    ) -> None:
        super(RelativeContainer, self).__init__(**kwargs)
        self.children: list[RenderObject] = []
        self.graph = DependencyGraph[RenderObject, str]().add_node(self)
        self.offsets: dict[RenderObject, XY] = {}
        self.constraints: list[ConstraintTuple] = []

    def add_child(
        self,
        child: RenderObject,
        offset: XY = (0, 0),
        **kwargs: Unpack[Relative],
    ) -> Self:
        if child in self.children:
            raise ValueError("Child already added")
        self.children.append(child)
        for relation, target in kwargs.items():
            self.graph.add_edge(target, child, relation)  # type: ignore
        self.offsets[child] = offset
        return self

    def add_constraint(
        self,
        obj: RenderObject,
        **kwargs: Unpack[Constraint],
    ) -> Self:
        for relation, target in kwargs.items():
            self.constraints.append((obj, relation, target))  # type: ignore
        return self

    @property
    @override
    def content_width(self) -> int:
        return self.infer_size()[0] if self.children else 0

    @property
    @override
    def content_height(self) -> int:
        return self.infer_size()[1] if self.children else 0

    def infer_size(self) -> XY:
        boxes = self._setup_boxes()
        x = LinearPolynomial(x=1)
        y = LinearPolynomial(y=1)
        w = LinearPolynomial(w=1)
        h = LinearPolynomial(h=1)
        size = self._infer_size(boxes, x, y, w, h)
        return round(size[w.var]), round(size[h.var])

    def _setup_boxes(self) -> dict[RenderObject, Box]:
        # TODO: Remove objects outside of container
        # e.g. A is align_left and align_top of container, B is left of A.
        #      If B not removed, A cannot meet the original requirement.
        x = LinearPolynomial(x=1)
        y = LinearPolynomial(y=1)
        w = LinearPolynomial(w=1)
        h = LinearPolynomial(h=1)
        undef = LinearPolynomial(undef=1)

        boxes: dict[RenderObject, Box] = {self: Box.of_size(x, y, w, h)}
        for obj in self.graph.topological_sort():
            if obj is self:
                continue

            # initialize x, y with undefined values
            obj_box = boxes.get(
                obj, Box.of_size(undef, undef, obj.width, obj.height))
            for pred in self.graph.get_predecessors(obj):
                for relative in self.graph.get_edges(pred, obj):
                    obj_box = obj_box.relative_to(boxes[pred], relative)
            # check if x, y are defined
            if obj_box.x1 is undef or obj_box.y1 is undef:
                raise ValueError(f"Could not resolve position of object: "
                                 f"{obj}(x={obj_box.x1}, y={obj_box.y1})")
            # apply offset
            boxes[obj] = obj_box.offset(*self.offsets.get(obj, (0, 0)))

        # remove temporary self box
        del boxes[self]
        return boxes

    def _infer_size(
        self,
        boxes: dict[RenderObject, Box],
        x: LinearPolynomial,
        y: LinearPolynomial,
        w: LinearPolynomial,
        h: LinearPolynomial,
    ) -> dict[str, float]:
        box_list = list(boxes.values())
        x1 = list(map(lambda b: b.x1, box_list))
        y1 = list(map(lambda b: b.y1, box_list))
        x2 = list(map(lambda b: b.x2, box_list))
        y2 = list(map(lambda b: b.y2, box_list))
        x1_x, x1_w = partition(lambda x: not x.contains_symbol(w), x1)
        y1_y, y1_h = partition(lambda x: not x.contains_symbol(h), y1)
        x2_x, x2_w = partition(lambda x: not x.contains_symbol(w), x2)
        y2_y, y2_h = partition(lambda x: not x.contains_symbol(h), y2)
        min_x1 = min(x1_x or x1_w)
        min_y1 = min(y1_y or y1_h)
        max_x2 = max(x2_w or x2_x)
        max_y2 = max(y2_h or y2_y)
        width = max_x2 - min_x1
        height = max_y2 - min_y1

        width_c = width.const if width.is_const else -1
        height_c = height.const if height.is_const else -1

        for obj_from, constraint, obj_to in self.constraints:
            box_from, box_to = boxes[obj_from], boxes[obj_to]
            in_eq = box_from.constrain(box_to, constraint)
            # TODO: handle not solvable or less_than case
            if in_eq.solvable and in_eq.var in [w.var, h.var]:
                var, greater, bound = in_eq.solve()
                if greater and var == w.var:
                    width_c = max(width_c, bound)
                elif greater and var == h.var:
                    height_c = max(height_c, bound)

        if width_c < 0 or height_c < 0:
            raise ValueError(
                f"Could not resolve size of container: w={width}, h={height}")

        x_eval = [x.eval(x=0, y=0, w=width_c, h=height_c) for x in x1 + x2]
        y_eval = [y.eval(x=0, y=0, w=width_c, h=height_c) for y in y1 + y2]
        x_offset = -min(x_eval) if min(x_eval) < 0 else 0
        y_offset = -min(y_eval) if min(y_eval) < 0 else 0
        return {
            x.var: x_offset,
            y.var: y_offset,
            w.var: width_c,
            h.var: height_c,
        }

    @override
    def render_content(self) -> RenderImage:
        if len(self.children) == 0:
            return RenderImage.empty(0, 0)

        x = LinearPolynomial(x=1)
        y = LinearPolynomial(y=1)
        w = LinearPolynomial(w=1)
        h = LinearPolynomial(h=1)

        boxes = self._setup_boxes()
        size = self._infer_size(boxes, x, y, w, h)

        im = RenderImage.empty(round(size[w.var]), round(size[h.var]))
        for obj, box in boxes.items():
            x = box.x1.eval(**size)
            y = box.y1.eval(**size)
            im = im.paste(x=round(x), y=round(y), im=obj.render())
        return im
