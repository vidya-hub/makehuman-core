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


def export(human, filepath, format=None, **kw):
    """Export ``human`` to ``filepath``. Format inferred from extension if not given."""
    fmt = (format or os.path.splitext(filepath)[1].lstrip(".")).lower()
    fn = _EXPORTERS.get(fmt)
    if fn is None:
        raise ValueError(
            f"Unsupported export format {fmt!r}; use one of {sorted(set(_EXPORTERS))}")
    return fn(human, filepath, **kw)


def _ensure_dir(filepath):
    d = os.path.dirname(os.path.abspath(filepath))
    if d and not os.path.exists(d):
        os.makedirs(d)
