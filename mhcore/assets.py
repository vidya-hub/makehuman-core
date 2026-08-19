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
_FILE_KINDS = {
    "poses": ("poses", "*.bvh"),
    "expressions": ("expressions", "*.mhpose"),
}
_COMPARE_BONE = "upperleg02.L"
_face_units = None


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
    if kind in _FILE_KINDS:
        return _search_dirs(*_FILE_KINDS[kind])
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


def adapt_all_proxies(human, fit_to_posed=False):
    """Refit every attached proxy (clothes/hair/eyes/…) to the current body.

    loadMeshAndObject only loads the authored OBJ. The GUI's proxy chooser
    calls proxy.update() on every modifier change; we have to do that here.
    """
    for pxy in human.getProxies(includeHumanProxy=True):
        if pxy is None or getattr(pxy, "object", None) is None:
            continue
        obj = pxy.object
        mesh = obj.getSeedMesh() if hasattr(obj, "getSeedMesh") else None
        if mesh is None:
            mesh = obj.mesh
        pxy.update(mesh, fit_to_posed)
        mesh.update()


def equip_clothes(human, path):
    p = _load_proxy(human, path, "Clothes")
    human.addClothesProxy(p)
    _apply(human)
    return p.uuid


def unequip_clothes(human, path):
    """Remove a single equipped clothing item, matched by its .mhclo path."""
    import getpath
    target = getpath.canonicalPath(path)
    for uuid, pxy in dict(human.clothesProxies).items():
        if pxy is not None and getpath.canonicalPath(pxy.file) == target:
            human.removeClothesProxy(uuid)
            _apply(human)
            return True
    return False


def _apply(human, fit_to_posed=False):
    human.applyAllTargets()
    adapt_all_proxies(human, fit_to_posed=fit_to_posed)


def unequip_all_clothes(human):
    for uuid in list(human.clothesProxies.keys()):
        human.removeClothesProxy(uuid)
    _apply(human)


def unequip_hair(human):
    human.setHairProxy(None)
    _apply(human)


def equip_hair(human, path):
    human.setHairProxy(_load_proxy(human, path, "Hair"))
    _apply(human)


def equip_eyes(human, path):
    human.setEyesProxy(_load_proxy(human, path, "Eyes"))
    _apply(human)


def equip_eyebrows(human, path):
    human.setEyebrowsProxy(_load_proxy(human, path, "Eyebrows"))
    _apply(human)


def equip_eyelashes(human, path):
    human.setEyelashesProxy(_load_proxy(human, path, "Eyelashes"))
    _apply(human)


def equip_teeth(human, path):
    human.setTeethProxy(_load_proxy(human, path, "Teeth"))
    _apply(human)


def equip_tongue(human, path):
    human.setTongueProxy(_load_proxy(human, path, "Tongue"))
    _apply(human)


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
    """Load a .bvh/.mhp pose onto the base skeleton and skin the mesh."""
    if not bvh_path:
        _clear_pose(human)
        state(human)["pose"] = None
        expr = state(human).get("expression")
        if expr:
            _apply_expression(human, expr)
        return
    _apply_pose(human, bvh_path)
    state(human)["pose"] = bvh_path
    expr = state(human).get("expression")
    if expr:
        _apply_expression(human, expr)


def set_expression(human, mhpose_path):
    """Blend a .mhpose facial expression onto the current pose."""
    if not mhpose_path:
        _clear_expression(human)
        state(human)["expression"] = None
        return
    _apply_expression(human, mhpose_path)
    state(human)["expression"] = mhpose_path


def _apply_pose(human, filepath):
    import bvh as bvh_mod
    import animation
    import numpy.linalg as la

    ext = os.path.splitext(filepath)[1].lower()
    skel = human.getBaseSkeleton()
    if skel is None:
        raise RuntimeError("No base skeleton; cannot apply a pose")

    if ext == ".mhp":
        anim = animation.loadPoseFromMhpFile(filepath, skel)
    elif ext == ".bvh":
        bvh_file = bvh_mod.load(filepath, convertFromZUp="auto")
        if _COMPARE_BONE not in bvh_file.joints:
            raise ValueError(
                "BVH does not use MakeHuman's default rig: %s" % filepath)
        anim = bvh_file.createAnimationTrack(skel)
        bvh_joint = bvh_file.joints[_COMPARE_BONE]
        bvh_len = float(la.norm(bvh_joint.children[0].position - bvh_joint.position))
        if bvh_len:
            scale = float(skel.getBone(_COMPARE_BONE).length) / bvh_len
            posedata = anim.getAtFramePos(0, noBake=True)
            posedata[0, :3, 3] = scale * posedata[0, :3, 3]
            anim.resetBaked()
    else:
        raise ValueError("Unknown pose file type: %s" % ext)

    human.addAnimation(anim)
    human.setActiveAnimation(anim.name)
    human.setToFrame(0, update=False)
    human.setPosed(True)
    adapt_all_proxies(human, fit_to_posed=True)


def _clear_pose(human):
    if human.hasAnimation("expr-lib-pose"):
        human.removeAnimation("expr-lib-pose")
    human.resetToRestPose()


def _face_pose_units(human):
    global _face_units
    if _face_units is not None:
        return _face_units
    import json
    from collections import OrderedDict
    import bvh as bvh_mod
    import animation
    import getpath

    path = getpath.getSysDataPath("poseunits/face-poseunits.bvh")
    base_bvh = bvh_mod.load(path, allowTranslation="none")
    base_anim = base_bvh.createAnimationTrack(
        human.getBaseSkeleton(), name="Expression-Face-PoseUnits")
    mapping = json.load(
        open(getpath.getSysDataPath("poseunits/face-poseunits.json"),
             "r", encoding="utf-8"),
        object_pairs_hook=OrderedDict)["framemapping"]
    if len(mapping) != base_bvh.frameCount:
        raise RuntimeError("face pose-unit BVH/JSON frame count mismatch")
    unit = animation.PoseUnit(base_anim.name, base_anim._data, mapping)
    idxs = sorted({b for lst in unit.getAffectedBones() for b in lst})
    _face_units = (unit, idxs)
    return _face_units


def _current_unmodified_pose(human):
    pose = human.getActiveAnimation()
    if pose is not None and getattr(pose, "pose_backref", None) is not None:
        return pose.pose_backref
    return pose


def _apply_expression(human, mhpose_path):
    import animation

    unit, face_idxs = _face_pose_units(human)
    new_pose = animation.poseFromUnitPose("expr-lib-pose", mhpose_path, unit)
    current = _current_unmodified_pose(human)
    if current is None:
        mixed = new_pose
        mixed.pose_backref = None
    else:
        mixed = animation.mixPoses(current, new_pose, face_idxs)
        mixed.pose_backref = current
    mixed.name = "expr-lib-pose"
    human.addAnimation(mixed)
    human.setActiveAnimation("expr-lib-pose")
    human.setPosed(True)
    human.refreshPose()
    adapt_all_proxies(human, fit_to_posed=True)


def _clear_expression(human):
    org = _current_unmodified_pose(human)
    if org is None:
        human.setActiveAnimation(None)
    elif human.hasAnimation(org.name):
        human.setActiveAnimation(org.name)
    else:
        human.addAnimation(org)
        human.setActiveAnimation(org.name)
    if human.hasAnimation("expr-lib-pose"):
        human.removeAnimation("expr-lib-pose")
    human.refreshPose(updateIfInRest=True)
