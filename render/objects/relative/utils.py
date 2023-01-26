from __future__ import annotations

from typing import Any, Callable, Generic, Iterable, TypeVar, Union
from typing_extensions import Self

Linear = Union[int, float, "LinearPolynomial"]
T = TypeVar("T")
Node = TypeVar("Node")  # Node in a graph
Edge = TypeVar("Edge")  # Edge in a graph


class LinearPolynomial:

    def __init__(self, const: float = 0.0, **coef: float) -> None:
        self.const = const
        self.symbols = coef

    @classmethod
    def of_const(cls, const: float) -> Self:
        return cls(const)

    def __add__(self, other: Linear) -> Self:
        if isinstance(other, LinearPolynomial):
            keys = set(self.symbols.keys()) | set(other.symbols.keys())
            coef = {
                key: self.symbols.get(key, 0) + other.symbols.get(key, 0)
                for key in keys
            }
            coef = {key: value for key, value in coef.items() if value != 0.0}
            return LinearPolynomial(self.const + other.const, **coef)
        elif isinstance(other, (int, float)):
            return LinearPolynomial(self.const + other, **self.symbols)
        else:
            return NotImplemented

    def __radd__(self, other: Linear) -> Self:
        return self + other

    def __sub__(self, other: Linear) -> Self:
        return self + (-other)

    def __neg__(self) -> Self:
        return LinearPolynomial(
            -self.const, **{key: -coef
                            for key, coef in self.symbols.items()})

    def __mul__(self, other: int | float) -> Self:
        if isinstance(other, (int, float)):
            return LinearPolynomial(
                self.const * other,
                **{key: coef * other
                   for key, coef in self.symbols.items()})
        else:
            return NotImplemented

    def __truediv__(self, other: int | float) -> Self:
        if isinstance(other, (int, float)):
            return LinearPolynomial(
                self.const / other,
                **{key: coef / other
                   for key, coef in self.symbols.items()})
        else:
            return NotImplemented

    def __floordiv__(self, other: int | float) -> Self:
        if isinstance(other, (int, float)):
            return LinearPolynomial(
                self.const // other,
                **{key: coef // other
                   for key, coef in self.symbols.items()})
        else:
            return NotImplemented

    def __lt__(self, other: Linear) -> bool:
        """Note: This is not exact. Just for finding the minimum."""
        if isinstance(other, (int, float)):
            return self.const < other and all(c <= 0
                                              for c in self.symbols.values())
        elif isinstance(other, LinearPolynomial):
            return self - other < 0
        else:
            return NotImplemented

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, LinearPolynomial):
            return self.const == other.const and self.symbols == other.symbols
        elif isinstance(other, (int, float)):
            return self.const == other and len(self.symbols) == 0
        else:
            return NotImplemented

    def __repr__(self) -> str:
        return f"LinearPolynomial({self.const}, {' '.join(f'{coef}:{key}' for key, coef in self.symbols.items())})"

    def __str__(self) -> str:
        def _symbol(key, coef):
            if coef == 1:
                return f"{key}"
            elif coef == -1:
                return f"-{key}"
            else:
                return f"{coef}{key}"

        if self.is_const:
            return str(self.const)
        else:
            const = f"{self.const} + " if self.const != 0 else ""
            terms = " + ".join(
                _symbol(key, coef) for key, coef in self.symbols.items())
            return (const + terms).lstrip("+ ").replace("+ -", "- ")

    def eval(self, **values: float) -> float:
        return self.const + sum(coef * values[key]
                                for key, coef in self.symbols.items())

    def contains_symbol(self, symbol: str | Self) -> bool:
        if isinstance(symbol, str):
            return symbol in self.symbols
        elif isinstance(symbol, LinearPolynomial):
            return all(key in self.symbols for key in symbol.symbols)
        else:
            raise TypeError(f"Invalid type: {type(symbol)}")

    @property
    def is_const(self) -> bool:
        return len(self.symbols) == 0

    @property
    def is_variable(self) -> bool:
        return (len(self.symbols) == 1 and self.const == 0
                and next(iter(self.symbols.values())) == 1)

    @property
    def var(self) -> str:
        if not self.is_variable:
            raise ValueError("Not a variable")
        return next(iter(self.symbols.keys()))


class Inequality(LinearPolynomial):
    """Represents an inequality LinearPolynomial >= 0."""

    def __init__(self, const: float, **symbols: float) -> None:
        super().__init__(const, **symbols)

    @classmethod
    def of(cls, poly: LinearPolynomial) -> Self:
        return cls(poly.const, **poly.symbols)

    @classmethod
    def greater(cls, lhs: Linear, rhs: Linear) -> Self:
        """Return an inequality that lhs >= rhs."""
        if isinstance(lhs, (int, float)):
            lhs = LinearPolynomial.of_const(lhs)
        if isinstance(rhs, (int, float)):
            rhs = LinearPolynomial.of_const(rhs)
        return cls.of(lhs - rhs)

    @classmethod
    def less(cls, lhs: Linear, rhs: Linear) -> Self:
        return cls.greater(rhs, lhs)

    @property
    def solvable(self) -> bool:
        """Solvable if it has only one variable.
        
        Note:
            A stronger implementation is to use linear programming
            to solve a couple of inequalities.
            For simplicity, we just check if it has only one variable.
        """
        return len(self.symbols) == 1

    @property
    def var(self) -> str:
        return next(iter(self.symbols.keys()))

    def satisfy(self, **values: float) -> bool:
        """Check if the inequality is satisfied with the given values."""
        return self.eval(**values) >= 0

    def solve(self) -> tuple[str, bool, float]:
        """Solve the inequality with result in the form of 
        var >= value or var <= value.
        
        Returns:
            var: The variable name.
            greater: True if var >= value, False if var <= value.
            value: The value of the bound.

        Raises:
            ValueError: If the inequality is not solvable.
        """ 
        if not self.solvable:
            raise ValueError("Not solvable")
        var = self.var
        return var, self.symbols[var] > 0, -self.const / self.symbols[var]

    def __str__(self) -> str:
        return super().__str__() + " >= 0"


class Point:

    def __init__(self, x: LinearPolynomial, y: LinearPolynomial) -> None:
        self.x = x
        self.y = y

    @classmethod
    def of(cls, x: Linear, y: Linear) -> Self:
        return cls(
            x if isinstance(x, LinearPolynomial)
            else LinearPolynomial.of_const(x), y if isinstance(
                y, LinearPolynomial) else LinearPolynomial.of_const(y))

    def __str__(self) -> str:
        return f"Point({self.x}, {self.y})"

    def contains_symbol(self, symbol: str) -> bool:
        return self.x.contains_symbol(symbol) or self.y.contains_symbol(symbol)


class Box:

    def __init__(self, p1: Point, p2: Point) -> None:
        self.p1 = p1
        self.p2 = p2

    @classmethod
    def of_size(
        cls,
        x: Linear,
        y: Linear,
        w: Linear,
        h: Linear,
    ) -> Self:
        return cls(Point.of(x, y), Point.of(x + w, y + h))

    @property
    def w(self) -> LinearPolynomial:
        return self.p2.x - self.p1.x

    @property
    def h(self) -> LinearPolynomial:
        return self.p2.y - self.p1.y

    @property
    def x1(self) -> LinearPolynomial:
        return self.p1.x

    @property
    def x2(self) -> LinearPolynomial:
        return self.p2.x

    @property
    def y1(self) -> LinearPolynomial:
        return self.p1.y

    @property
    def y2(self) -> LinearPolynomial:
        return self.p2.y

    def above(self, other: Self) -> Self:
        return Box.of_size(self.p1.x, other.p1.y - self.h, self.w, self.h)

    def below(self, other: Self) -> Self:
        return Box.of_size(self.p1.x, other.p2.y, self.w, self.h)

    def left(self, other: Self) -> Self:
        return Box.of_size(other.p1.x - self.w, self.p1.y, self.w, self.h)

    def right(self, other: Self) -> Self:
        return Box.of_size(other.p2.x, self.p1.y, self.w, self.h)

    def align_top(self, other: Self) -> Self:
        return Box.of_size(self.p1.x, other.p1.y, self.w, self.h)

    def align_bottom(self, other: Self) -> Self:
        return Box.of_size(self.p1.x, other.p2.y - self.h, self.w, self.h)

    def align_left(self, other: Self) -> Self:
        return Box.of_size(other.p1.x, self.p1.y, self.w, self.h)

    def align_right(self, other: Self) -> Self:
        return Box.of_size(other.p2.x - self.w, self.p1.y, self.w, self.h)

    def center_vertical(self, other: Self) -> Self:
        return Box.of_size(self.p1.x, other.p1.y + (other.h - self.h) / 2,
                           self.w, self.h)

    def center_horizontal(self, other: Self) -> Self:
        return Box.of_size(other.p1.x + (other.w - self.w) / 2, self.p1.y,
                           self.w, self.h)

    def center(self, other: Self) -> Self:
        return Box.of_size(other.p1.x + (other.w - self.w) / 2,
                           other.p1.y + (other.h - self.h) / 2, self.w, self.h)

    def prior_to(self, other: Self) -> Self:
        """A dummy method to make self dependent on other 
        so that other will be overlaid.
        
        """
        return self

    def relative_to(
        self,
        other: Self,
        relative_type: str,
    ) -> Self:
        """Get an updated box as if self is placed relative to other."""
        if not hasattr(self, relative_type):
            raise ValueError(f"Invalid relative type: {relative_type}")
        return getattr(self, relative_type)(other)

    def constrain(self, other: Self, constraint: str) -> Inequality:
        """Get an inequality that constrains self to other."""
        if constraint == "left":
            return Inequality.less(self.x2, other.x1)
        elif constraint == "right":
            return Inequality.greater(self.x1, other.x2)
        elif constraint == "above":
            return Inequality.less(self.y2, other.y1)
        elif constraint == "below":
            return Inequality.greater(self.y1, other.y2)
        else:
            raise ValueError(f"Invalid constraint: {constraint}")

    def offset(self, x: Linear, y: Linear) -> Self:
        return Box.of_size(self.p1.x + x, self.p1.y + y, self.w, self.h)

    def __str__(self) -> str:
        return f"Box({self.p1}, {self.p2})"


class DependencyGraph(Generic[Node, Edge]):
    """A dependency graph between objects. Supports topological sorting."""

    def __init__(self) -> None:
        # node -> successors
        self.graph: dict[Any, set[Any]] = {}
        # node -> predecessors
        self.reverse_graph: dict[Any, set[Any]] = {}
        # (node, successor) -> edges
        self.edge: dict[tuple[Any, Any], set[Edge]] = {}

    def add_node(self, node: Node) -> Self:
        self.graph.setdefault(node, set())
        self.reverse_graph.setdefault(node, set())
        return self

    def add_edge(self, node: Node, successor: Node, edge: Edge) -> Self:
        self.graph.setdefault(node, set()).add(successor)
        self.reverse_graph.setdefault(node, set())
        self.graph.setdefault(successor, set())
        self.reverse_graph.setdefault(successor, set()).add(node)
        self.edge.setdefault((node, successor), set()).add(edge)
        return self

    def get_predecessors(self, node: Node) -> set[Node]:
        return self.reverse_graph[node]

    def get_edges(self, node: Node, successor: Node) -> set[Edge]:
        return self.edge[(node, successor)]

    def topological_sort(self) -> list[Node]:
        """Perform topological sort on the graph.
        
        Returns:
            A list of nodes in topological order.

        Raises:
            ValueError: If the graph contains a cycle.
        """
        reverse_graph = {
            node: set(predecessors)
            for node, predecessors in self.reverse_graph.items()
        }
        queue = [
            node for node, predecessors in reverse_graph.items()
            if len(predecessors) == 0
        ]
        result = []
        while queue:
            node = queue.pop()
            result.append(node)
            for successor in self.graph.get(node, []):
                reverse_graph[successor].remove(node)
                if len(reverse_graph[successor]) == 0:
                    queue.append(successor)
        if len(result) != len(self.graph):
            raise ValueError("Cyclic dependency graph")
        return result


def partition(
    predicate: Callable[[T], bool],
    iterable: Iterable[T],
) -> tuple[list[T], list[T]]:
    """Partition an iterable into two lists based on a predicate.
    
    Args:
        predicate: A function that takes an item and returns a boolean.
        iterable: An iterable to partition.

    Returns:
        A tuple of (list of items satisfying the predicate,
        list of items not satisfying the predicate).
    """
    x, y = [], []
    for item in iterable:
        (x if predicate(item) else y).append(item)
    return x, y
