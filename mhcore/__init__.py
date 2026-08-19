"""mhcore -- a GUI-free (no Qt, no OpenGL) MakeHuman core library.

Load a human, set modifiers, equip assets, and save/export -- all without the
MakeHuman GUI. Built by vendoring the unmodified MakeHuman source (``_vendor/``)
and driving it through a headless application shim.

Quick start::

    import mhcore
    h = mhcore.new_human()
    h.set_gender(1.0); h.set_age(0.5)
    h.export("hero.obj")
    h.save_mhm("hero.mhm")
"""

from __future__ import annotations

__version__ = "0.1.1"

from .bootstrap import init, new_human as _new_base_human, data_path


def new_human():
    """Create a fresh character and return an :class:`mhcore.api.MHHuman`."""
    from .api import MHHuman
    return MHHuman(_new_base_human())


__all__ = ["init", "new_human", "data_path", "MHHuman"]


def __getattr__(name):
    if name == "MHHuman":
        from .api import MHHuman
        return MHHuman
    raise AttributeError(name)
