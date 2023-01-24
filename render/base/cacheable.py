from typing import Any, Callable, Dict, Generic, Iterable, TypeVar
from typing_extensions import Self

T = TypeVar("T")


class Cacheable:

    def __init__(self, *parent: "Cacheable") -> None:
        self.__cache__: Dict[str, Any] = {}
        self.__cache_parent__ = list(parent)

    def clear_cache(self) -> None:
        self.__cache__ = {}
        for p in self.__cache_parent__:
            p.clear_cache()

    def add_parent(self, parent: "Cacheable") -> None:
        self.__cache_parent__.append(parent)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}"


def clear_cache_after(f: Callable):
    def wrapper(self, *args, **kwargs):
        result = f(self, *args, **kwargs)
        self.clear_cache()
        return result

    return wrapper


class CacheableList(list[T], Cacheable):

    def __init__(self, iterable: Iterable[T] = (), *parent: Cacheable) -> None:
        list.__init__(self, iterable)
        Cacheable.__init__(self, *parent)
        for item in iterable:
            if isinstance(item, Cacheable):
                item.add_parent(self)

    def __repr__(self) -> str:
        return Cacheable.__repr__(self)

    __setitem__ = clear_cache_after(list.__setitem__)
    __delitem__ = clear_cache_after(list.__delitem__)
    __add__ = clear_cache_after(list.__add__)
    __iadd__ = clear_cache_after(list.__iadd__)
    __mul__ = clear_cache_after(list.__mul__)
    __imul__ = clear_cache_after(list.__imul__)
    __rmul__ = clear_cache_after(list.__rmul__)
    append = clear_cache_after(list.append)
    extend = clear_cache_after(list.extend)
    insert = clear_cache_after(list.insert)
    pop = clear_cache_after(list.pop)
    remove = clear_cache_after(list.remove)
    reverse = clear_cache_after(list.reverse)
    sort = clear_cache_after(list.sort)


def cached(func: Callable[[Any], T]) -> Callable[[Cacheable], T]:
    key = func.__name__

    def wrapper(self):
        if not isinstance(self, Cacheable):
            raise TypeError("@cached can only be used on Cacheable objects.")
        if key in self.__cache__:
            return self.__cache__[key]
        return self.__cache__.setdefault(key, func(self))

    return wrapper


class volatile(Generic[T]):
    """A context manager that used in Cacheable.__init__ method to create volatile properties."""

    @classmethod
    def create_property(cls, obj: Cacheable, attr: str, initial: T) -> None:
        """Create a property named `attr` on `obj.__class__` that is volatile.
        
        the getter will return obj._attr, the setter will set obj._attr and notify obj of the change.
        """

        protected_attr = "_" + attr
        setattr(obj, protected_attr, initial)

        # if already a property, don't override
        if not isinstance(getattr(obj.__class__, attr, None), property):

            def getter(self: Cacheable) -> T:
                return getattr(self, protected_attr)

            def setter(self: Cacheable, value: T):
                if not hasattr(self, protected_attr) or value != getattr(
                        self, protected_attr):
                    setattr(self, protected_attr, value)
                    self.clear_cache()

            setattr(obj.__class__, attr, property(getter, setter))

    def list(self, value: Iterable[T]) -> CacheableList[T]:
        return CacheableList(value, self.obj)

    def __init__(self, obj: Cacheable) -> None:
        self.obj = obj

    def __enter__(self) -> Self:
        self.attr_names = list(self.obj.__dict__.keys())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        # compare which attributes have been created,
        # create property for each new attribute
        new_attr = {}
        for attr in self.obj.__dict__:
            if not attr.startswith("_") and attr not in self.attr_names:
                new_attr[attr] = getattr(self.obj, attr)
        for attr, value in new_attr.items():
            if isinstance(value, list) and not isinstance(value, CacheableList):
                raise TypeError(f"{attr} is a list, use self.{attr} = volatile.list(value).")
            self.create_property(self.obj, attr, value)
