from __future__ import annotations

from typing import Any, Callable, Generic, Iterable, TypeVar
from typing_extensions import Self

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


class Cacheable:

    def __init__(self, *parent: Cacheable) -> None:
        self.__cache__: dict[str, Any] = {}
        self.__cache_parent__ = list(parent)

    def clear_cache(self) -> None:
        self.__cache__ = {}
        for p in self.__cache_parent__:
            p.clear_cache()

    def add_parent(self, parent: Cacheable) -> Self:
        if parent not in self.__cache_parent__:
            self.__cache_parent__.append(parent)
        return self

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}"


class CacheableList(list[T], Cacheable):

    def __init__(self, iterable: Iterable[T] = (), *parent: Cacheable) -> None:
        list.__init__(self, iterable)
        Cacheable.__init__(self, *parent)
        for item in iterable:
            if isinstance(item, Cacheable):
                item.add_parent(self)

    def __repr__(self) -> str:
        return Cacheable.__repr__(self) + list.__repr__(self)

    def _list_update(f: Callable):  # type: ignore
        def wrapper(self, *args, **kwargs):
            result = f(self, *args, **kwargs)
            self.clear_cache()
            for item in self:
                if isinstance(item, Cacheable):
                    item.add_parent(self)
            return result

        return wrapper

    __setitem__ = _list_update(list.__setitem__)
    __delitem__ = _list_update(list.__delitem__)
    __add__ = _list_update(list.__add__)
    __iadd__ = _list_update(list.__iadd__)
    __mul__ = _list_update(list.__mul__)
    __imul__ = _list_update(list.__imul__)
    __rmul__ = _list_update(list.__rmul__)
    append = _list_update(list.append)
    extend = _list_update(list.extend)
    insert = _list_update(list.insert)
    pop = _list_update(list.pop)
    remove = _list_update(list.remove)
    reverse = _list_update(list.reverse)
    sort = _list_update(list.sort)


class CacheableDict(dict[K, V], Cacheable):

    def __init__(self, dict_: dict[K, V] = {}, *parent: Cacheable) -> None:
        dict.__init__(self, dict_)
        Cacheable.__init__(self, *parent)
        for key, value in dict_.items():
            if isinstance(value, Cacheable):
                value.add_parent(self)
            if isinstance(key, Cacheable):
                raise TypeError("CacheableDict keys must be immutable.")

    def __repr__(self) -> str:
        return Cacheable.__repr__(self) + dict.__repr__(self)

    def _dict_update(f: Callable):  # type: ignore
        def wrapper(self, *args, **kwargs):
            result = f(self, *args, **kwargs)
            self.clear_cache()
            for key, value in self.items():
                if isinstance(value, Cacheable):
                    value.add_parent(self)
                if isinstance(key, Cacheable):
                    raise TypeError("CacheableDict keys must be immutable.")
            return result

        return wrapper

    __setitem__ = _dict_update(dict.__setitem__)
    __delitem__ = _dict_update(dict.__delitem__)
    clear = _dict_update(dict.clear)
    pop = _dict_update(dict.pop)
    popitem = _dict_update(dict.popitem)
    setdefault = _dict_update(dict.setdefault)
    update = _dict_update(dict.update)


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

    def list(self, value: Iterable[T] | None = None) -> CacheableList[T]:
        value = value or []
        return CacheableList(value, self.obj)

    def dict(self, value: dict[K, V] | None = None) -> CacheableDict[K, V]:
        value = value or {}
        return CacheableDict(value, self.obj)

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
            if isinstance(value,
                          list) and not isinstance(value, CacheableList):
                raise TypeError(
                    f"{attr} is a list, use self.{attr} = volatile.list(value)."
                )
            if isinstance(value,
                          dict) and not isinstance(value, CacheableDict):
                raise TypeError(
                    f"{attr} is a dict, use self.{attr} = volatile.dict(value)."
                )
            self.create_property(self.obj, attr, value)
