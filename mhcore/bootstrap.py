"""Headless bootstrap: make the vendored MakeHuman core importable and usable
without Qt or OpenGL, and create a base Human.

Order matters:
1. Put the vendored source dirs on sys.path (mirroring MakeHuman's flat layout).
2. chdir to the repo root so getpath's ``getSysPath()`` (which returns ``./<x>``)
   resolves to the bundled ``data/``.
3. Install the GUI/GL shims (fake ``mh``/``gui``/``gui3d``/``qtui``/``glmodule``).
4. Install a HeadlessApp as ``core.G.app``.
5. Register the re-homed .mhm save/load handlers.
6. Load the base mesh + default skeleton into a Human.
"""

from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)                 # repo root (contains data/, _vendor/)
_VENDOR = os.path.join(_ROOT, "_vendor")
_DATA = os.path.join(_ROOT, "data")

# MakeHuman's flat import layout: these dirs are all added to sys.path so that
# modules import each other by bare name (import human, import module3d, ...).
_VENDOR_PATHS = [
    _VENDOR,
    os.path.join(_VENDOR, "lib"),
    os.path.join(_VENDOR, "apps"),
    os.path.join(_VENDOR, "shared"),
    os.path.join(_VENDOR, "apps", "gui"),
    os.path.join(_VENDOR, "core"),
    # Exporters live under _vendor/_exporters as importable packages
    # (_vendor itself is on the path, so `import _exporters.fbx.mh2fbx` works).
]

_initialized = False


def data_path(sub: str = "") -> str:
    return os.path.join(_DATA, sub) if sub else _DATA


def _setup_syspath() -> None:
    for p in reversed(_VENDOR_PATHS):
        if p not in sys.path:
            sys.path.insert(0, p)


def init() -> None:
    """Idempotently prepare the headless environment (no Human created yet)."""
    global _initialized
    if _initialized:
        return

    _setup_syspath()

    # makehuman.py main() normally sets these; provide values so the .mhm
    # header comment is clean instead of "UNKNOWN:UNKNOWN".
    os.environ.setdefault("MH_VERSION", "mhcore")
    os.environ.setdefault("MH_SHORT_VERSION", "mhcore")
    os.environ.setdefault("MH_MESH_VERSION", "hm08")

    # Quiet numpy like makehuman.py main() does.
    import numpy
    numpy.seterr(all="ignore")

    # MakeHuman prints a startup line to stdout on first import of `core` and
    # logs verbosely. Keep the caller's stdout pristine -- this is essential
    # when mhcore backs a stdio server (e.g. an MCP server), where anything on
    # stdout corrupts the protocol -- and route/quiet the noise to stderr.
    import contextlib
    with contextlib.redirect_stdout(sys.stderr):
        import getpath  # vendored, pure

        # MakeHuman's getSysPath returns "./<sub>" (relative to cwd, because the
        # app chdirs to its install dir). As a library we must not chdir the
        # caller's process, so point the system path at the bundled repo root.
        # getSysDataPath() calls getSysPath() by module-global lookup, so
        # patching this one function is sufficient.
        def _sys_path(subPath=""):
            p = os.path.join(_ROOT, subPath) if subPath else _ROOT
            return getpath.formatPath(p)
        getpath.getSysPath = _sys_path

        # Shims must be installed before importing any module that imports mh.
        from . import _shims
        _shims.install(getpath)

        # Install the headless application object on the global G.
        from core import G  # -> _vendor/lib/core.py
        from .app import HeadlessApp
        if not isinstance(getattr(G, "app", None), HeadlessApp):
            G.app = HeadlessApp()

        # Re-home the .mhm persistence handlers (skeleton/material/proxy/...).
        from . import handlers
        handlers.register_all(G.app)

        _quiet_logging()

    _initialized = True


def _quiet_logging():
    """Reduce MakeHuman's very chatty DEBUG logging (goes to stderr).

    Set MHCORE_VERBOSE=1 to keep the full MakeHuman log output.
    """
    if os.environ.get("MHCORE_VERBOSE"):
        return
    import logging
    logging.getLogger().setLevel(logging.WARNING)


def new_human():
    """Create and return a base Human (base mesh + default skeleton, modifiers)."""
    init()

    from core import G
    import human as human_mod
    import files3d
    import getpath
    import skeleton as skeleton_mod

    base_obj = getpath.getSysDataPath("3dobjs/base.obj")
    mesh = files3d.loadMesh(base_obj, maxFaces=5)
    hu = human_mod.Human(mesh)
    G.app.selectedHuman = hu

    # Default skeleton (as MHApplication.loadHuman does).
    base_skel = skeleton_mod.load(getpath.getSysDataPath("rigs/default.mhskel"),
                                  hu.meshData)
    hu.setBaseSkeleton(base_skel)

    # Load the modifier definitions (macro + detail) so getModifier works.
    _load_modifiers(hu)

    # The default skin material has autoBlendSkin=True, which lazily reads
    # litsphere PNGs through the Qt image backend when its diffuse colour is
    # queried (e.g. during export). Disable it so the headless geometry path
    # never needs Qt; a plain diffuse colour is used instead. A user who calls
    # set_skin() with a real .mhmat gets that material as-is.
    try:
        hu.material.autoBlendSkin = False
    except Exception:
        pass

    return hu


def _load_modifiers(hu) -> None:
    """Load modifier definitions from the data/modifiers/*.json files."""
    import humanmodifier
    import getpath

    modifier_files = [
        "modifiers/modeling_modifiers.json",
        "modifiers/measurement_modifiers.json",
    ]
    for mf in modifier_files:
        path = getpath.getSysDataPath(mf)
        modifiers = humanmodifier.loadModifiers(path, hu)
    # After loading, apply default macro state so a valid mesh exists.
    hu.applyAllTargets()
