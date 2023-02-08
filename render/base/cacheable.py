from __future__ import annotations

import inspect
import sys
from types import TracebackType
from typing import Any, Callable, Generic, Iterable, Type, TypeVar

from typing_extensions import Literal, Self

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

if sys.version_info < (3, 9):
    # Python 3.9+ has built-in support for generic collections.
    # This is a backport for Python 3.8 and below.
    from collections import UserDict as _UserDict
    from collections import UserList as _UserList

    class UserList(_UserList, Generic[T]):

        def __class_getitem__(cls, item: T) -> Type[_UserList[T]]:
            return cls

    class UserDict(_UserDict, Generic[K, V]):

        def __class_getitem__(cls, item: tuple[K, V]) -> Type[_UserDict[K, V]]:
            return cls
else:
    from collections import UserDict, UserList


class Cacheable:
    """Supports caching return value of properties and methods.

    Cache can be cleared recursively by calling `clear_cache()`.

    Attributes:
        _cache_: Mapping from names to cached values.
        _cache_parent_: List of parent Cacheable objects.
    """

    def __init__(self, *parent: Cacheable) -> None:
        self._cache_: dict[str, Any] = {}
        self._cache_parent_ = list(parent)

    def clear_cache(self) -> None:
        self._cache_ = {}
        for p in self._cache_parent_:
            p.clear_cache()

    def add_parent(self, parent: Cacheable) -> Self:
        if parent not in self._cache_parent_:
            self._cache_parent_.append(parent)
        return self

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}"

    def replace(self, other: Cacheable) -> None:
        """Replace this object with another object at all parent occurences.

        Used when an object inside a container needs to be replaced.
        """
        for parent in self._cache_parent_:
            if isinstance(parent, CacheableList):
                for i, item in enumerate(parent):
                    if item is self:
                        parent[i] = other
                        other.add_parent(parent)
            elif isinstance(parent, CacheableDict):
                for k, item in parent.items():
                    if item is self:
                        parent[k] = other
                        other.add_parent(parent)
            else:
                raise TypeError(
                    f"Unsupported parent type: {type(parent).__name__}")
        self._cache_parent_ = []


def _assert_not_list_or_dict(value: Any) -> None:
    """Raise TypeError if value is a list or dict.

    Modifying a list or dict in place will not trigger the cache update.
    Thus, we do not allow them to be used as values in Cacheable.
    """
    if isinstance(value, list) and not isinstance(value, CacheableList):
        raise TypeError(
            "Builtin list is not supported. Use CacheableList instead.")
    if isinstance(value, dict) and not isinstance(value, CacheableDict):
        raise TypeError(
            "Builtin dict is not supported. Use CacheableDict instead.")


def _list_update(func: Callable[..., T]) -> Callable[..., T]:
    """Apply to list methods that may change the list."""

    def wrapper(self: CacheableList, *args, **kwargs) -> T:
        result = func(self, *args, **kwargs)
        self.clear_cache()
        for item in self:
            if isinstance(item, Cacheable):
                item.add_parent(self)
            _assert_not_list_or_dict(item)
        return result

    return wrapper


class CacheableList(UserList[T], Cacheable):
    """A cacheable list sensitive to changes in its items."""

    def __init__(self, iterable: Iterable[T], *parent: Cacheable) -> None:
        Cacheable.__init__(self, *parent)
        UserList[T].__init__(self, iterable)
        for item in iterable:
            if isinstance(item, Cacheable):
                item.add_parent(self)
            _assert_not_list_or_dict(item)

    def __repr__(self) -> str:
        return Cacheable.__repr__(self) + UserList[T].__repr__(self)

    __setitem__ = _list_update(UserList[T].__setitem__)
    __delitem__ = _list_update(UserList[T].__delitem__)
    __add__ = _list_update(UserList[T].__add__)
    __iadd__ = _list_update(UserList[T].__iadd__)
    __mul__ = _list_update(UserList[T].__mul__)
    __imul__ = _list_update(UserList[T].__imul__)
    __rmul__ = _list_update(UserList[T].__rmul__)
    append = _list_update(UserList[T].append)
    extend = _list_update(UserList[T].extend)
    insert = _list_update(UserList[T].insert)
    pop = _list_update(UserList[T].pop)
    remove = _list_update(UserList[T].remove)
    reverse = _list_update(UserList[T].reverse)
    sort = _list_update(UserList[T].sort)


def _dict_update(func: Callable[..., T]) -> Callable[..., T]:
    """Apply to dict methods that may change the dict values."""

    def wrapper(self: CacheableDict, *args, **kwargs) -> T:
        result = func(self, *args, **kwargs)
        self.clear_cache()
        for key, value in self.items():
            if isinstance(value, Cacheable):
                value.add_parent(self)
            _assert_not_list_or_dict(value)
            if isinstance(key, Cacheable):
                raise TypeError(
                    f"CacheableDict keys cannot be cacheable: {key!r}")
        return result

    return wrapper


class CacheableDict(UserDict[K, V], Cacheable):
    """A cacheable dict sensitive to changes in its values.

    Raises:
        TypeError: If a key is a Cacheable object.
    """

    def __init__(self, mapping: dict[K, V], *parent: Cacheable) -> None:
        mapping = mapping or {}
        Cacheable.__init__(self, *parent)
        UserDict[K, V].__init__(self, mapping)
        for key, value in mapping.items():
            if isinstance(value, Cacheable):
                value.add_parent(self)
            _assert_not_list_or_dict(value)
            if isinstance(key, Cacheable):
                raise TypeError(
                    f"CacheableDict keys cannot be cacheable: {key!r}")

    def __repr__(self) -> str:
        return Cacheable.__repr__(self) + UserDict[K, V].__repr__(self)

    __setitem__ = _dict_update(UserDict[K, V].__setitem__)
    __delitem__ = _dict_update(UserDict[K, V].__delitem__)
    clear = _dict_update(UserDict[K, V].clear)
    pop = _dict_update(UserDict[K, V].pop)
    popitem = _dict_update(UserDict[K, V].popitem)
    setdefault = _dict_update(UserDict[K, V].setdefault)
    update = _dict_update(UserDict[K, V].update)


def cached(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to cache the return value of a method.

    Raises:
        TypeError: If the object of decorated method is not a Cacheable object.
    """
    key = func.__name__

    def wrapper(self: Cacheable) -> T:
        if not isinstance(self, Cacheable):
            raise TypeError(
                f"@cached must be used on a Cacheable object: {type(self)}")
        if key in self._cache_:
            return self._cache_[key]
        return self._cache_.setdefault(key, func(self))

    return wrapper


class volatile:
    """A context manager that used in Cacheable.__init__ method
    to create volatile properties.

    Attributes:
        obj: The Cacheable object.

    Raises:
        TypeError: If volatile attribute is a python list or dict.
        RuntimeError: If volatile is not called from Cacheable.__init__.
    """

    @classmethod
    def create_property(cls, obj: Cacheable, attr: str, initial: T) -> T:
        """Create a property named `attr` on `obj.__class__` that is volatile.

        `property.getter` will return `obj._attr` and
        `property.setter` will set `obj._attr` and notify `obj` of the change.
        """

        protected_attr = "_" + attr
        setattr(obj, protected_attr, initial)

        # if already a property, don't override
        if not isinstance(getattr(obj.__class__, attr, None), property):

            def getter(self: Cacheable) -> T:
                return getattr(self, protected_attr)

            def setter(self: Cacheable, value: T) -> None:
                _assert_not_list_or_dict(value)
                if not hasattr(self, protected_attr) or value != getattr(
                        self, protected_attr):
                    setattr(self, protected_attr, value)
                    self.clear_cache()

            setattr(obj.__class__, attr, property(getter, setter))

        # return this just to suppress pylance warning
        return initial

    def list(self, value: Iterable[T] | None = None) -> CacheableList[T]:
        value = value or []
        return CacheableList(value, self.obj)

    def dict(self, value: dict[K, V] | None = None) -> CacheableDict[K, V]:
        value = value or {}
        return CacheableDict(value, self.obj)

    def __init__(self, obj: Cacheable) -> None:
        self.obj = obj
        self.attr_names: list[str] = []

        frame = inspect.currentframe()
        back = None if frame is None else frame.f_back
        if back is None:
            raise RuntimeError(
                "volatile must be used in Cacheable.__init__: None")
        caller = back.f_code.co_name
        if caller != "__init__":
            raise RuntimeError(
                f"volatile must be used in Cacheable.__init__: {caller}")

    def __enter__(self) -> Self:
        self.attr_names = list(self.obj.__dict__.keys())
        return self

    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        # compare which attributes have been created,
        # create property for each new attribute
        new_attr = {}
        for attr in self.obj.__dict__:
            if not attr.startswith("_") and attr not in self.attr_names:
                new_attr[attr] = getattr(self.obj, attr)
        for attr, value in new_attr.items():
            _assert_not_list_or_dict(value)
            self.create_property(self.obj, attr, value)
        return False  # don't suppress exceptions
