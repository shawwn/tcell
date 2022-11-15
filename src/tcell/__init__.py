from __future__ import annotations
import dataclasses
from typing import *
import weakref
import collections.abc as std
import inspect

# read version from installed package
from importlib.metadata import version
__version__ = version(__name__)

del version

_T = TypeVar("_T")
_KT = TypeVar("_KT")
_VT = TypeVar("_VT")
_T_co = TypeVar("_T_co", covariant=True)
_VT_co = TypeVar("_VT_co", covariant=True)

def scheme_add_to_table(cells: MutableMapping[_KT, _VT], key: _KT, val: _VT, constant: bool = False):
    cells[key] = val

def scheme_lookup_in_table(t: MutableMapping[_KT, _VT], key: _KT) -> Optional[_VT]:
    return t.get(key, None)

class Reference(Generic[_T]):
    def __init__(self, getter: Callable[[], _T], *, setter: Optional[Callable[[_T], Any]] = None, finalizer: Optional[Callable[[], Any]] = None):
        self.getter = getter
        self.setter = setter
        if finalizer:
            self._del = weakref.finalize(self, lambda finalizer: finalizer(), finalizer)
        else:
            self._del = lambda: None

    @property
    def disposed(self):
        return self.getter() is None

    def __del__(self):
        self.dispose()

    def dispose(self):
        if not self.disposed:
            self.getter = lambda: None
            self.setter = None
        self._del()

    def __call__(self, *value):
        if value:
            if not self.setter:
                raise TypeError("Reference does not support assignment")
            return self.setter(*value)
        else:
            return self.getter()

def make_weakref(v: _T, callback: Callable[[], Any] = None) -> Callable[[], _T]:
    if isinstance(v, weakref.ref):
        return Reference(v, finalizer=callback)
    if inspect.ismethod(v):
        return weakref.WeakMethod(v, lambda ref: callback())
    try:
        return weakref.ref(v, lambda ref: callback())
    except TypeError:
        return Reference(lambda: v, finalizer=callback)

@dataclasses.dataclass
class Ephemeron(Generic[_KT, _VT]):
    key: Callable[[], _KT]
    val: Callable[[], _VT]

    def __bool__(self):
        return self.key() is not None and self.val() is not None

def scheme_make_ephemeron(key: _KT, val: _VT) -> Ephemeron[_KT, _VT]:
    def finalizer():
        nonlocal val
        # print("ephemeron finalizer for ", val)
        val = None
    return Ephemeron(make_weakref(key, finalizer),
                     Reference(lambda: val, finalizer=finalizer))

def scheme_ephemeron_key(eph: Ephemeron[_KT, _VT]) -> _KT:
    return eph.key()

def scheme_ephemeron_value(eph: Ephemeron[_KT, _VT]) -> _VT:
    return eph.val()

@dataclasses.dataclass
class ThreadCell(Generic[_T]):
    def_val: _T
    inherited: bool
    assigned: bool = False

    def __hash__(self):
        return hash(id(self))

@dataclasses.dataclass
class ThreadCellTable(std.MutableMapping[ThreadCell[_VT_co], Ephemeron[ThreadCell[_VT_co], _VT_co]]):
    buckets: MutableMapping[ThreadCell[_VT_co], Ephemeron[ThreadCell[_VT_co], _VT_co]]

    def __setitem__(self, __k: ThreadCell[_VT_co], __v: Ephemeron[ThreadCell[_VT_co], _VT_co]):
        self.buckets[__k] = __v

    def __delitem__(self, __v: ThreadCell[_VT_co]):
        del self.buckets[__v]

    def __getitem__(self, __k: ThreadCell[_VT_co]) -> Ephemeron[ThreadCell[_VT_co], _VT_co]:
        return self.buckets[__k]

    def __len__(self) -> int:
        return len(self.buckets)

    def __iter__(self) -> Iterator[ThreadCell[_VT_co]]:
        return iter(self.buckets)

def scheme_make_thread_cell(def_val: _T, inherited: bool) -> ThreadCell[_T]:
    return ThreadCell(def_val, inherited)

def do_thread_cell_get(cell: ThreadCell[_T], cells: ThreadCellTable) -> _T:
    if cell.assigned:
        v = scheme_lookup_in_table(cells, cell)
        if v:
            return scheme_ephemeron_value(v)
    return cell.def_val

def scheme_thread_cell_get(cell: ThreadCell[_T], cells: ThreadCellTable) -> _T:
    if not cell.assigned:
        return cell.def_val
    else:
        return do_thread_cell_get(cell, cells)

def scheme_thread_cell_set(cell: ThreadCell[_T_co], cells: ThreadCellTable, v: _T_co):
    if not cell.assigned:
        cell.assigned = True
    v = scheme_make_ephemeron(cell, v)
    scheme_add_to_table(cells, cell, v, False)

def scheme_empty_cell_table() -> ThreadCellTable:
    return ThreadCellTable(weakref.WeakKeyDictionary())

def inherit_cells(cells: ThreadCellTable[_KT, _VT_co], t: Optional[ThreadCellTable[_KT, _VT_co]] = None, inherited: bool = True) -> ThreadCellTable[_KT, _VT_co]:
    # if cells is None:
    #     cells = scheme_current_thread.cell_values
    if t is None:
        t = scheme_empty_cell_table()
    for cell, val in cells.buckets.items():
        if cell and val:
            if cell.inherited == inherited:
                scheme_add_to_table(t, cell, val, False)
    return t

def scheme_inherit_cells(cells: ThreadCellTable[_KT, _VT_co]) -> ThreadCellTable[_KT, _VT_co]:
    return inherit_cells(cells, None, True)
