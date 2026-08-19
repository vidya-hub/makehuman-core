"""Headless wrappers around MakeHuman's exporters.

The exporter *functions* (mh2obj.exportObj, mh2fbx.exportFbx,
mh2collada.exportCollada) are already GUI-free -- they take a Human via an
ExportConfig and write a file. Only the plugin ``build()``/TaskView wrappers
touch Qt, which we skip entirely.
"""

from __future__ import annotations

import os


# Mesh-orientation mixin: the FBX/DAE exporters read these off the config.
# Ported verbatim (minus the Qt widgets) from the export plugins' Config
# subclasses so output matches the GUI exporters.
class _OrientationMixin:
    yUpFaceZ = True
    yUpFaceX = False
    zUpFaceNegY = False
    zUpFaceX = False
    localY = True
    localX = False
    localG = False

    @property
    def meshOrientation(self):
        if self.yUpFaceZ:
            return "yUpFaceZ"
        if self.yUpFaceX:
            return "yUpFaceX"
        if self.zUpFaceNegY:
            return "zUpFaceNegY"
        if self.zUpFaceX:
            return "zUpFaceX"
        return "yUpFaceZ"

    @property
    def localBoneAxis(self):
        if self.localY:
            return "y"
        if self.localX:
            return "x"
        if self.localG:
            return "g"
        return "y"


def _configure(cfg, human, scale, unit, feet_on_ground, use_normals):
    cfg.setHuman(human)
    cfg.scale = scale
    cfg.unit = unit
    cfg.feetOnGround = feet_on_ground
    cfg.useNormals = use_normals
    cfg.hiddenGeom = False
    return cfg


def _obj_config(human, scale=1.0, unit="dm", feet_on_ground=True, use_normals=True):
    import export as export_mod  # -> _vendor/core/export.py
    cfg = export_mod.ExportConfig()
    cfg.useRelPaths = True
    return _configure(cfg, human, scale, unit, feet_on_ground, use_normals)


def _fbx_config(human, scale=1.0, unit="dm", feet_on_ground=True, use_normals=True):
    import export as export_mod

    class FbxConfig(_OrientationMixin, export_mod.ExportConfig):
        pass

    cfg = FbxConfig()
    cfg.useRelPaths = False
    cfg.useMaterials = True
    cfg.binary = True
    return _configure(cfg, human, scale, unit, feet_on_ground, use_normals)


def _dae_config(human, scale=1.0, unit="dm", feet_on_ground=True, use_normals=True):
    import export as export_mod

    class DaeConfig(_OrientationMixin, export_mod.ExportConfig):
        pass

    cfg = DaeConfig()
    cfg.useRelPaths = True
    cfg.facePoseUnits = False
    return _configure(cfg, human, scale, unit, feet_on_ground, use_normals)


def export_obj(human, filepath, **kw):
    from _exporters.obj import mh2obj
    cfg = _obj_config(human, **kw)
    _ensure_dir(filepath)
    mh2obj.exportObj(filepath, cfg)
    return filepath


def export_fbx(human, filepath, **kw):
    from _exporters.fbx import mh2fbx
    cfg = _fbx_config(human, **kw)
    _ensure_dir(filepath)
    mh2fbx.exportFbx(filepath, cfg)
    return filepath


def export_dae(human, filepath, **kw):
    from _exporters.dae import mh2collada
    cfg = _dae_config(human, **kw)
    _ensure_dir(filepath)
    mh2collada.exportCollada(filepath, cfg)
    return filepath


_EXPORTERS = {
    "obj": export_obj,
    "fbx": export_fbx,
    "dae": export_dae,
    "collada": export_dae,
}


def export(human, filepath, format=None, rig="deform", scale=None, unit=None,
           feet_on_ground=True, **kw):
    """Export ``human`` to ``filepath``.

    Defaults are Blender-friendly: metres (``scale=0.1``, ``unit="m"``) so the
    character imports at real size, and for FBX/DAE a clean, skinned rig is
    bound automatically.

    rig: "deform" (default clean game rig), "full" (163-bone default rig),
    "none" (unrigged mesh), or a path to a .mhskel file. Ignored for OBJ.
    scale/unit: override the metre defaults (e.g. scale=1.0 unit="dm" for the
    old decimetre output, or scale=0.01 for centimetre/Unreal).
    """
    fmt = (format or os.path.splitext(filepath)[1].lstrip(".")).lower()
    fn = _EXPORTERS.get(fmt)
    if fn is None:
        raise ValueError(
            f"Unsupported export format {fmt!r}; use one of {sorted(set(_EXPORTERS))}")

    # MakeHuman works in decimetres. FBX writes a unit factor and DAE writes a
    # <unit> tag, so at scale=1.0 both import at real size (~1.7 m) in Blender
    # (verified). OBJ carries no unit metadata, so it must be pre-scaled to
    # metres (0.1) or it comes in 10x too big.
    if scale is None:
        scale = 0.1 if fmt == "obj" else 1.0
    if unit is None:
        unit = "m" if fmt == "obj" else "dm"
    kw.update(scale=scale, unit=unit, feet_on_ground=feet_on_ground)

    rigged = fmt in ("fbx", "dae", "collada") and rig not in (None, "none")
    if not rigged:
        return fn(human, filepath, **kw)

    # Bind a clean, fitted, weighted skeleton just for the export, then restore
    # whatever skeleton the human had so export stays side-effect-free.
    from . import assets
    prev = human.getSkeleton()
    skel = assets.resolve_export_skeleton(human, rig)
    human.setSkeleton(skel)
    try:
        return fn(human, filepath, **kw)
    finally:
        human.setSkeleton(prev)


def _ensure_dir(filepath):
    d = os.path.dirname(os.path.abspath(filepath))
    if d and not os.path.exists(d):
        os.makedirs(d)
