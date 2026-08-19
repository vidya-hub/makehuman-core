"""Asset discovery and equipping (clothes/hair/eyes/skin) -- GUI-free.

Discovery scans the bundled system data dirs plus the per-user data dir for the
relevant file types. Equipping uses the underlying non-GUI calls:
``proxy.loadProxy`` + ``human.set*Proxy`` / ``human.addClothesProxy`` for
proxies, and ``material.fromFile`` + ``human.setMaterial`` for skins.
"""

from __future__ import annotations

import fnmatch
import os


# type -> (data subdir, file glob)
_PROXY_KINDS = {
    "clothes": ("clothes", "*.mhclo"),
    "hair": ("hair", "*.mhclo"),
    "eyes": ("eyes", "*.mhclo"),
    "eyebrows": ("eyebrows", "*.mhclo"),
    "eyelashes": ("eyelashes", "*.mhclo"),
    "teeth": ("teeth", "*.mhclo"),
    "tongue": ("tongue", "*.mhclo"),
}
_SKIN_DIR = ("skins", "*.mhmat")


def _find(root, glob):
    matches = []
    if not os.path.isdir(root):
        return matches
    for base, _dirs, files in os.walk(root):
        for fn in fnmatch.filter(files, glob):
            matches.append(os.path.join(base, fn))
    return matches


def _search_dirs(subdir, glob):
    import getpath
    results = []
    for root in (getpath.getSysDataPath(subdir), getpath.getDataPath(subdir)):
        results.extend(_find(root, glob))
    # de-dup preserving order
    seen = set()
    out = []
    for p in results:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def list_available(kind):
    kind = kind.lower()
    if kind == "skins":
        return _search_dirs(*_SKIN_DIR)
    if kind not in _PROXY_KINDS:
        raise ValueError(f"Unknown asset kind {kind!r}")
    return _search_dirs(*_PROXY_KINDS[kind])


# -- equipping -------------------------------------------------------------

def _load_proxy(human, path, proxy_type):
    import proxy as proxy_mod
    p = proxy_mod.loadProxy(human, path, type=proxy_type)
    # loadProxy only parses the proxy definition; the fitted mesh + Object
    # (proxy.object) must be built before the human can attach it. The GUI
    # chooser plugins do this via loadMeshAndObject.
    p.loadMeshAndObject(human)
    return p


def equip_clothes(human, path):
    p = _load_proxy(human, path, "Clothes")
    human.addClothesProxy(p)
    human.applyAllTargets()
    return p.uuid


def equip_hair(human, path):
    human.setHairProxy(_load_proxy(human, path, "Hair"))
    human.applyAllTargets()


def equip_eyes(human, path):
    human.setEyesProxy(_load_proxy(human, path, "Eyes"))
    human.applyAllTargets()


def equip_eyebrows(human, path):
    human.setEyebrowsProxy(_load_proxy(human, path, "Eyebrows"))
    human.applyAllTargets()


def equip_eyelashes(human, path):
    human.setEyelashesProxy(_load_proxy(human, path, "Eyelashes"))
    human.applyAllTargets()


def equip_teeth(human, path):
    human.setTeethProxy(_load_proxy(human, path, "Teeth"))
    human.applyAllTargets()


def equip_tongue(human, path):
    human.setTongueProxy(_load_proxy(human, path, "Tongue"))
    human.applyAllTargets()


def set_skin(human, path):
    import material
    mat = material.fromFile(path)
    # Keep headless: a file-referenced skin should not trigger the Qt image
    # blender when its colour is read during export.
    try:
        mat.autoBlendSkin = False
    except Exception:
        pass
    human.setMaterial(mat)
    return mat


def state(human):
    """Per-human side state for file paths not otherwise recoverable
    (skeleton/pose/expression source files)."""
    st = getattr(human, "_mhcore_state", None)
    if st is None:
        st = {"skeleton": None, "pose": None, "expression": None}
        human._mhcore_state = st
    return st


def set_skeleton(human, path):
    import skeleton as skeleton_mod
    skel = skeleton_mod.load(path, human.meshData)
    human.setSkeleton(skel)
    human.applyAllTargets()
    state(human)["skeleton"] = path
    return skel


def set_pose(human, bvh_path):
    # Record for .mhm round-trip. Full BVH retargeting/application is a
    # documented follow-up; the pose reference is preserved in the .mhm.
    state(human)["pose"] = bvh_path


def set_expression(human, bvh_path):
    state(human)["expression"] = bvh_path
