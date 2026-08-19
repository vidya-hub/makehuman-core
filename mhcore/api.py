"""High-level, GUI-free character API.

Wraps the vendored MakeHuman ``Human`` with an ergonomic surface that mirrors
what the MCP server already speaks (set_gender/set_age/apply_modifier/...).
"""

from __future__ import annotations

import os

from . import export as _export
from . import assets as _assets


def _clamp01(v):
    return 0.0 if v < 0.0 else 1.0 if v > 1.0 else float(v)


class MHHuman:
    """A MakeHuman character you can shape, dress, save and export headlessly."""

    def __init__(self, human):
        self._h = human

    # -- underlying object -------------------------------------------------
    @property
    def human(self):
        """The wrapped vendored ``Human`` (escape hatch for advanced use)."""
        return self._h

    def _apply(self):
        self._h.applyAllTargets()

    # -- body macros (0.0 - 1.0) ------------------------------------------
    def set_gender(self, value):
        self._h.setGender(_clamp01(value)); self._apply(); return self

    def set_age(self, value):
        self._h.setAge(_clamp01(value)); self._apply(); return self

    def set_weight(self, value):
        self._h.setWeight(_clamp01(value)); self._apply(); return self

    def set_muscle(self, value):
        self._h.setMuscle(_clamp01(value)); self._apply(); return self

    def set_height(self, value):
        self._h.setHeight(_clamp01(value)); self._apply(); return self

    # -- detail modifiers --------------------------------------------------
    def list_modifiers(self):
        return sorted(self._h.getModifierNames())

    def get_modifier(self, name):
        return self._h.getModifier(name)

    def apply_modifier(self, name, power):
        modifier = self._h.getModifier(name)
        if modifier is None:
            raise KeyError(f"No such modifier: {name!r}")
        modifier.setValue(power)
        self._apply()
        return self

    def get_applied_targets(self):
        targets = {}
        for target, value in self._h.targetsDetailStack.items():
            key = target.split("/data/targets/")[-1]
            targets[key] = value
        return targets

    # -- assets ------------------------------------------------------------
    def list_available(self, kind):
        """List installed asset paths. kind: clothes/hair/eyes/eyebrows/
        eyelashes/teeth/tongue/skins."""
        return _assets.list_available(kind)

    def equip_clothes(self, path):
        return _assets.equip_clothes(self._h, path)

    def unequip_clothes(self, path):
        return _assets.unequip_clothes(self._h, path)

    def unequip_all_clothes(self):
        _assets.unequip_all_clothes(self._h); return self

    def unequip_hair(self):
        _assets.unequip_hair(self._h); return self

    def equip_hair(self, path):
        _assets.equip_hair(self._h, path); return self

    def equip_eyes(self, path):
        _assets.equip_eyes(self._h, path); return self

    def equip_eyebrows(self, path):
        _assets.equip_eyebrows(self._h, path); return self

    def equip_eyelashes(self, path):
        _assets.equip_eyelashes(self._h, path); return self

    def equip_teeth(self, path):
        _assets.equip_teeth(self._h, path); return self

    def equip_tongue(self, path):
        _assets.equip_tongue(self._h, path); return self

    def set_skin(self, path):
        _assets.set_skin(self._h, path); return self

    def set_skeleton(self, path):
        _assets.set_skeleton(self._h, path); return self

    def set_pose(self, bvh_path):
        _assets.set_pose(self._h, bvh_path); return self

    def set_expression(self, bvh_path):
        _assets.set_expression(self._h, bvh_path); return self

    def get_equipped_clothes(self):
        return [p.file for p in self._h.clothesProxies.values()] \
            if hasattr(self._h, "clothesProxies") else []

    # -- export ------------------------------------------------------------
    def export(self, filepath, format=None, **kw):
        """Export to OBJ/FBX/DAE (format inferred from extension if omitted)."""
        return _export.export(self._h, filepath, format=format, **kw)

    # -- persistence (.mhm) ------------------------------------------------
    def save_mhm(self, filepath):
        if not filepath.lower().endswith(".mhm"):
            filepath += ".mhm"
        d = os.path.dirname(os.path.abspath(filepath))
        if d and not os.path.exists(d):
            os.makedirs(d)
        self._h.save(filepath)
        return filepath

    def load_mhm(self, filepath):
        self._h.load(filepath)
        return self

    # -- introspection -----------------------------------------------------
    @property
    def vertex_count(self):
        return int(self._h.meshData.coord.shape[0])

    def __repr__(self):
        return f"<MHHuman verts={self.vertex_count} modifiers={len(self.list_modifiers())}>"
