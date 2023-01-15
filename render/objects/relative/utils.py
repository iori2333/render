from typing import (Any, Callable, Dict, Generic, Iterable, List, Set, Tuple,
                    TypeVar, Union)
from typing_extensions import Self

Linear = Union[int, float, "LinearPolynomial"]
T = TypeVar("T")
Node = TypeVar("Node")
Edge = TypeVar("Edge")


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

    def __mul__(self, other: Union[int, float]) -> Self:
        if isinstance(other, (int, float)):
            return LinearPolynomial(
                self.const * other,
                **{key: coef * other
                   for key, coef in self.symbols.items()})
        else:
            return NotImplemented

    def __truediv__(self, other: Union[int, float]) -> Self:
        if isinstance(other, (int, float)):
            return LinearPolynomial(
                self.const / other,
                **{key: coef / other
                   for key, coef in self.symbols.items()})
        else:
            return NotImplemented

    def __floordiv__(self, other: Union[int, float]) -> Self:
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
            return self.const < other and all(c <= 0 for c in self.symbols.values())
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

    def contains_symbol(self, symbol: Union[str, Self]) -> bool:
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
        """A dummy method to make self dependent on other so that other will be overlaid."""
        return self

    def relative_to(self, other: Self, relative_type: str) -> Self:
        if not hasattr(self, relative_type):
            raise ValueError(f"Invalid relative type: {relative_type}")
        return getattr(self, relative_type)(other)

    def __str__(self) -> str:
        return f"Box({self.p1}, {self.p2})"


class DependencyGraph(Generic[Node, Edge]):
    """A dependency graph between objects. Performs topological sorting."""
    def __init__(self) -> None:
        # node -> successors
        self.graph: Dict[Any, Set[Any]] = {}
        # node -> predecessors
        self.reverse_graph: Dict[Any, Set[Any]] = {}
        # (node, successor) -> edges
        self.edge: Dict[Tuple[Any, Any], Set[Edge]] = {}

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

    def get_predecessors(self, node: Node) -> Set[Node]:
        return self.reverse_graph[node]

    def get_edges(self, node: Node, successor: Node) -> Set[Edge]:
        return self.edge[(node, successor)]

    def topological_sort(self) -> List[Node]:
        """Returns a topological sort of the graph, or raises an exception if the graph is cyclic."""
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
) -> Tuple[List[T], List[T]]:
    x, y = [], []
    for item in iterable:
        (x if predicate(item) else y).append(item)
    return x, y
