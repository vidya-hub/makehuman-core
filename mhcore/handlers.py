"""Re-homed .mhm save/load handlers (headless).

In the full GUI these are registered by library plugins (skeleton, material,
the proxy choosers, pose, expression). Here we register equivalent handlers on
the HeadlessApp that read/write the identical .mhm lines directly against the
Human, so .mhm files round-trip without the plugin/GUI system.

.mhm lines handled (in addition to the modifier/camera lines written by
Human.save itself):

    skeleton <relpath>
    <proxytype> <name> <uuid>          # clothes/hair/eyes/eyebrows/eyelashes/teeth/tongue/proxymeshes
    skinMaterial <relpath>
    material <name> <uuid> <relpath>
    pose <relpath>
    expression <relpath>
    clothesHideFaces <bool>            # accepted, no-op (a GUI-only render flag)
"""

from __future__ import annotations

import fnmatch
import os

_registered = False

# proxy .mhm keyword -> equip function name in mhcore.assets
_PROXY_EQUIP = {
    "clothes": "equip_clothes",
    "hair": "equip_hair",
    "eyes": "equip_eyes",
    "eyebrows": "equip_eyebrows",
    "eyelashes": "equip_eyelashes",
    "teeth": "equip_teeth",
    "tongue": "equip_tongue",
}

# dirs scanned to resolve a proxy UUID back to a file on load
_PROXY_DIRS = ["clothes", "hair", "eyes", "eyebrows", "eyelashes", "teeth",
               "tongue", "proxymeshes"]

_uuid_index = None  # lazily built {uuid: filepath}


# -- path helpers ----------------------------------------------------------

def _relpath(path):
    import getpath
    if not path:
        return path
    return getpath.getRelativePath(path)


def _resolve(relpath):
    """Resolve a relative asset path (as stored in a .mhm) to an absolute file."""
    import getpath
    if os.path.isabs(relpath) and os.path.isfile(relpath):
        return relpath
    for cand in (getpath.getSysDataPath(relpath), getpath.getDataPath(relpath)):
        if os.path.isfile(cand):
            return cand
    found = getpath.thoroughFindFile(relpath, [getpath.getSysDataPath(),
                                               getpath.getDataPath()])
    return found if found and os.path.isfile(found) else None


def _build_uuid_index():
    global _uuid_index
    if _uuid_index is not None:
        return _uuid_index
    import getpath
    idx = {}
    for sub in _PROXY_DIRS:
        for root in (getpath.getSysDataPath(sub), getpath.getDataPath(sub)):
            if not os.path.isdir(root):
                continue
            for base, _d, files in os.walk(root):
                for fn in fnmatch.filter(files, "*.mhclo"):
                    fp = os.path.join(base, fn)
                    uuid = _read_mhclo_uuid(fp)
                    if uuid and uuid not in idx:
                        idx[uuid] = fp
    _uuid_index = idx
    return idx


def _read_mhclo_uuid(filepath):
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.startswith("uuid"):
                    return line[4:].strip()
                if line.startswith("verts") or line.startswith("v "):
                    break  # past the header
    except OSError:
        return None
    return None


def _proxy_by_uuid(uuid):
    return _build_uuid_index().get(uuid)


# -- save handlers ---------------------------------------------------------

def _save_skeleton(human, f):
    from . import assets
    st = assets.state(human)
    if human.getSkeleton() and st.get("skeleton"):
        f.write("skeleton %s\n" % _relpath(st["skeleton"]))


def _save_proxies(human, f):
    for pxy in human.getProxies(includeHumanProxy=True):
        if pxy is None:
            continue
        f.write("%s %s %s\n" % (pxy.type.lower(), pxy.name, pxy.getUuid()))


def _save_materials(human, f):
    mat = human.material
    if mat is not None and getattr(mat, "filename", None):
        f.write("skinMaterial %s\n" % _relpath(mat.filename))
    for pxy in human.getProxies(includeHumanProxy=True):
        if pxy is None:
            continue
        pmat = getattr(pxy, "material", None)
        if pmat is not None and getattr(pmat, "filename", None):
            f.write("material %s %s %s\n" % (pxy.name, pxy.getUuid(),
                                             _relpath(pmat.filename)))


def _save_pose_expression(human, f):
    from . import assets
    st = assets.state(human)
    if st.get("pose"):
        f.write("pose %s\n" % _relpath(st["pose"]))
    if st.get("expression"):
        f.write("expression %s\n" % _relpath(st["expression"]))


# -- load handlers ---------------------------------------------------------

def _load_skeleton(human, values, strict):
    if values[0] == "status" or len(values) < 2:
        return
    path = _resolve(values[1])
    if not path:
        if strict:
            raise RuntimeError("Could not resolve skeleton %s" % values[1])
        return
    from . import assets
    assets.set_skeleton(human, path)


def _load_proxy_line(human, values, strict):
    if values[0] == "status" or len(values) < 3:
        return
    ptype, _name, uuid = values[0], values[1], values[-1]
    path = _proxy_by_uuid(uuid)
    if not path:
        if strict:
            raise RuntimeError("Could not resolve %s proxy uuid %s" % (ptype, uuid))
        return
    from . import assets
    equip = getattr(assets, _PROXY_EQUIP.get(ptype, ""), None)
    if equip is not None:
        equip(human, path)


def _load_skin_material(human, values, strict):
    if values[0] == "status" or len(values) < 2:
        return
    path = _resolve(values[1])
    if path:
        from . import assets
        assets.set_skin(human, path)


def _load_proxy_material(human, values, strict):
    # material <name> <uuid> <relpath>
    if values[0] == "status" or len(values) < 4:
        return
    uuid, matrel = values[2], values[3]
    matpath = _resolve(matrel)
    if not matpath:
        return
    import material
    for pxy in human.getProxies(includeHumanProxy=True):
        if pxy is not None and pxy.getUuid() == uuid and pxy.object is not None:
            mat = material.fromFile(matpath)
            try:
                mat.autoBlendSkin = False
            except Exception:
                pass
            pxy.object.material = mat
            return


def _load_pose(human, values, strict):
    if values[0] == "status" or len(values) < 2:
        return
    from . import assets
    path = _resolve(values[1])
    if path:
        assets.set_pose(human, path)
        return
    assets.state(human)["pose"] = values[1]
    if strict:
        raise RuntimeError("Could not resolve pose %s" % values[1])


def _load_expression(human, values, strict):
    if values[0] == "status" or len(values) < 2:
        return
    from . import assets
    path = _resolve(values[1])
    if path:
        assets.set_expression(human, path)
        return
    assets.state(human)["expression"] = values[1]
    if strict:
        raise RuntimeError("Could not resolve expression %s" % values[1])


def _load_noop(human, values, strict):
    return


def register_all(app) -> None:
    global _registered
    if _registered:
        return

    # Save handlers (priority = positional insert order in the file).
    app.addSaveHandler(_save_skeleton, priority=5)
    app.addSaveHandler(_save_proxies, priority=6)
    app.addSaveHandler(_save_materials, priority=7)
    app.addSaveHandler(_save_pose_expression, priority=8)

    # Load handlers keyed by the .mhm line keyword.
    app.addLoadHandler("skeleton", _load_skeleton)
    for kw in _PROXY_EQUIP:
        app.addLoadHandler(kw, _load_proxy_line)
    app.addLoadHandler("proxymeshes", _load_proxy_line)
    app.addLoadHandler("skinMaterial", _load_skin_material)
    app.addLoadHandler("material", _load_proxy_material)
    app.addLoadHandler("pose", _load_pose)
    app.addLoadHandler("expression", _load_expression)
    app.addLoadHandler("clothesHideFaces", _load_noop)

    _registered = True
