"""GUI/GL shim modules for headless MakeHuman.

The unmodified MakeHuman source we vendor in ``_vendor/`` was written to run
inside a PyQt5 + OpenGL application. A handful of its modules do
``import mh`` / ``import gui`` / ``import gui3d`` / ``import qtui`` /
``import glmodule`` at import time. None of those are actually needed for the
character pipeline (load human, morph, save, export) -- that path is pure
numpy -- but the imports must resolve.

This module installs lightweight stand-ins in ``sys.modules`` *before* any
vendored module is imported, so the real Qt/GL modules are never loaded. The
only real functionality any of these stubs must provide is the pure path
helpers that ``mh`` normally re-exports from ``getpath``; everything GUI/GL is
a harmless no-op.

Call :func:`install` exactly once, early, from the bootstrap.
"""

from __future__ import annotations

import sys
import types


def _make_module(name: str) -> types.ModuleType:
    mod = types.ModuleType(name)
    mod.__mhcore_shim__ = True
    return mod


class _AnyAttr(types.ModuleType):
    """A module whose unknown attributes resolve to harmless no-op callables.

    Used for ``gui``/``gui3d``/``qtui``/``glmodule`` where vendored code may
    reference assorted names at import time but never actually exercises them
    in the headless path.
    """

    def __getattr__(self, item):
        if item.startswith("__") and item.endswith("__"):
            raise AttributeError(item)

        def _noop(*args, **kwargs):
            return None

        _noop.__name__ = item
        return _noop


def _install_mh(getpath) -> None:
    """Install the ``mh`` stub, re-exporting getpath's pure helpers."""
    mh = _make_module("mh")

    # Pure path helpers (the only part of mh the core path genuinely needs).
    mh.getPath = getpath.getPath
    mh.getDataPath = getpath.getDataPath
    mh.getSysDataPath = getpath.getSysDataPath
    mh.getSysPath = getpath.getSysPath

    # GUI/GL surface -> no-ops.
    def _noop(*args, **kwargs):
        return None

    for fn in ("redraw", "callAsync", "callAsyncThread", "grabScreen",
               "addPanels", "showPanels", "changeCategory", "changeTask",
               "setClearColor", "setCaption", "refreshLayout", "updatePickingBuffer"):
        setattr(mh, fn, _noop)

    # A few modules read mh.<Enum>/mh.cameras etc.; expose permissive stubs.
    mh.Keys = _AnyAttr("mh.Keys")
    mh.Buttons = _AnyAttr("mh.Buttons")
    mh.Modifiers = _AnyAttr("mh.Modifiers")

    sys.modules["mh"] = mh


def install(getpath) -> None:
    """Install all GUI/GL shims. ``getpath`` is the real vendored module."""
    if sys.modules.get("mh", None) is not None and getattr(
            sys.modules["mh"], "__mhcore_shim__", False):
        return  # already installed

    _install_mh(getpath)

    for name in ("gui", "gui3d", "qtui", "glmodule"):
        if name in sys.modules and not getattr(sys.modules[name], "__mhcore_shim__", False):
            continue
        mod = _AnyAttr(name)
        mod.__mhcore_shim__ = True
        sys.modules[name] = mod
