"""Backends the MCP tools run against.

Two implementations with the same method surface:

- ``LocalBackend`` drives the GUI-free ``mhcore`` library in-process. No running
  MakeHuman needed. This is the default.
- ``SocketBackend`` talks to a running MakeHuman over its socket bridge (the
  original behaviour), kept for driving an interactive GUI session.

Select with the ``MAKEHUMAN_BACKEND`` env var (``local`` or ``socket``).
Default is ``local`` when ``mhcore`` is importable, else ``socket``.
"""

from __future__ import annotations

import importlib.util
import os

from .client import MHClient, MakeHumanConnectionError, MakeHumanError


class BackendError(RuntimeError):
    pass


# --------------------------------------------------------------------------
# Local, in-process backend (mhcore)
# --------------------------------------------------------------------------

class LocalBackend:
    """In-process backend using the mhcore library (no running MakeHuman)."""

    name = "local"

    def __init__(self):
        self._human = None  # created lazily on first use

    def _h(self):
        if self._human is None:
            import mhcore
            self._human = mhcore.new_human()
        return self._human

    # -- status ------------------------------------------------------------
    def ping(self):
        h = self._h()
        return "OK: mhcore in-process backend ready (%d modifiers)." % len(
            h.list_modifiers())

    def reset(self):
        import mhcore
        self._human = mhcore.new_human()
        return "OK: new character."

    # -- macros ------------------------------------------------------------
    def set_macro(self, which, value):
        getattr(self._h(), "set_" + which)(value)
        return "OK"

    # -- modifiers ---------------------------------------------------------
    def list_modifiers(self):
        return self._h().list_modifiers()

    def apply_modifier(self, name, power):
        self._h().apply_modifier(name, power)
        return "OK"

    def get_applied_targets(self):
        return self._h().get_applied_targets()

    # -- assets ------------------------------------------------------------
    def list_available(self, kind):
        return self._h().list_available(kind)

    def equip(self, kind, path):
        getattr(self._h(), "equip_" + kind)(path)
        return "OK"

    def set_skin(self, path):
        self._h().set_skin(path)
        return "OK"

    def unequip_clothes(self, path):
        return "OK" if self._h().unequip_clothes(path) else "No matching clothing equipped."

    def unequip_all_clothes(self):
        self._h().unequip_all_clothes()
        return "OK"

    def unequip_hair(self):
        self._h().unequip_hair()
        return "OK"

    def get_equipped_clothes(self):
        return self._h().get_equipped_clothes()

    def set_pose(self, path):
        self._h().set_pose(path)
        return "OK"

    def set_expression(self, path):
        self._h().set_expression(path)
        return "OK"

    def set_skeleton(self, path):
        self._h().set_skeleton(path)
        return "OK"

    # -- persist / export --------------------------------------------------
    def save(self, path):
        return self._h().save_mhm(path)

    def load(self, path):
        self._h().load_mhm(path)
        return "OK"

    def export(self, path, fmt, rig="deform", scale=None, feet_on_ground=True):
        return self._h().export(path, format=fmt, rig=rig, scale=scale,
                                feet_on_ground=feet_on_ground)


# --------------------------------------------------------------------------
# Socket backend (running MakeHuman GUI)
# --------------------------------------------------------------------------

class SocketBackend:
    """Backend that calls a running MakeHuman over the socket bridge."""

    name = "socket"

    _EQUIP_FN = {
        "clothes": "equipClothes",
        "hair": "equipHair",
        "eyebrows": "equipEyebrows",
        "eyelashes": "equipEyelashes",
        "eyes": "equipEyes",
    }
    _LIST_FN = {
        "clothes": "getAvailableClothes",
        "hair": "getAvailableHair",
        "skins": "getAvailableSkins",
        "eyebrows": "getAvailableEyebrows",
        "eyelashes": "getAvailableEyelashes",
    }
    _EXPORT_FN = {"obj": "exportOBJ", "fbx": "exportFBX",
                  "dae": "exportDAE", "mhx2": "exportMHX2"}

    def __init__(self, host="127.0.0.1", port=12345):
        self._client = MHClient(host=host, port=port)

    def ping(self):
        self._client.ping()
        return "OK: MakeHuman is reachable over the socket."

    def set_macro(self, which, value):
        return self._client.call("set" + which.capitalize(), value=value)

    def list_modifiers(self):
        return self._client.call("getAvailableModifierNames")

    def apply_modifier(self, name, power):
        return self._client.call("applyModifier", modifier=name, power=power)

    def get_applied_targets(self):
        return self._client.call("getAppliedTargets")

    def list_available(self, kind):
        fn = self._LIST_FN.get(kind)
        if fn is None:
            raise BackendError(f"socket backend has no listing for {kind!r}")
        return self._client.call(fn)

    def equip(self, kind, path):
        fn = self._EQUIP_FN.get(kind)
        if fn is None:
            raise BackendError(f"socket backend cannot equip {kind!r}")
        return self._client.call(fn, path=path)

    def set_skin(self, path):
        return self._client.call("setSkin", path=path)

    def unequip_clothes(self, path):
        return self._client.call("unequipClothes", path=path)

    def unequip_all_clothes(self):
        return self._client.call("unequipAllClothes")

    def unequip_hair(self):
        return self._client.call("unequipHair")

    def get_equipped_clothes(self):
        return self._client.call("getEquippedClothes")

    def set_pose(self, path):
        raise BackendError("set_pose is only available on the local backend")

    def set_expression(self, path):
        raise BackendError("set_expression is only available on the local backend")

    def set_skeleton(self, path):
        raise BackendError("set_skeleton is only available on the local backend")

    def save(self, path):
        return self._client.call("saveMHM", path=path)

    def load(self, path):
        return self._client.call("loadMHM", path=path)

    def export(self, path, fmt, rig="deform", scale=None, feet_on_ground=True):
        # The GUI exporter uses its own config; rig/scale are local-backend only.
        fn = self._EXPORT_FN.get(fmt)
        if fn is None:
            raise BackendError(f"unsupported export format {fmt!r}")
        return self._client.call(fn, path=path)


# --------------------------------------------------------------------------
# selection
# --------------------------------------------------------------------------

def _mhcore_available():
    return importlib.util.find_spec("mhcore") is not None


def make_backend():
    choice = os.environ.get("MAKEHUMAN_BACKEND", "").strip().lower()
    if not choice:
        choice = "local" if _mhcore_available() else "socket"

    if choice == "local":
        if not _mhcore_available():
            raise BackendError(
                "MAKEHUMAN_BACKEND=local but mhcore is not installed. "
                "Install it: pip install -e /path/to/makehuman-core")
        return LocalBackend()
    if choice == "socket":
        return SocketBackend(
            host=os.environ.get("MAKEHUMAN_HOST", "127.0.0.1"),
            port=int(os.environ.get("MAKEHUMAN_PORT", "12345")))
    raise BackendError(f"Unknown MAKEHUMAN_BACKEND {choice!r} (use local or socket)")
