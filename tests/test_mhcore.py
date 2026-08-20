"""Tests for the GUI-free mhcore library.

These must pass in an environment with only numpy installed (no PyQt5, no
PyOpenGL) -- that is the core guarantee of the project.
"""

import os

import pytest

import mhcore


@pytest.fixture(scope="module")
def human():
    return mhcore.new_human()


def test_data_root_from_clone():
    assert os.path.isfile(mhcore.data_path("3dobjs/base.obj"))


def test_no_gui_dependencies_installed():
    # Guard: the whole point is that these are NOT required.
    for mod in ("PyQt5", "OpenGL"):
        with pytest.raises(ImportError):
            __import__(mod)


def test_base_human_loads(human):
    assert human.vertex_count > 10000
    mods = human.list_modifiers()
    assert len(mods) > 200
    assert "macrodetails/Gender" in mods


def test_macros_change_mesh():
    h = mhcore.new_human()
    before = h.human.meshData.coord.copy()
    h.set_gender(1.0).set_age(0.9).set_weight(0.9).set_muscle(0.9)
    after = h.human.meshData.coord
    assert not (before == after).all(), "setting macros should morph the mesh"


def test_apply_modifier_and_unknown():
    h = mhcore.new_human()
    h.apply_modifier("head/head-oval", 0.5)
    assert h.get_applied_targets()  # non-empty
    with pytest.raises(KeyError):
        h.apply_modifier("does/not-exist", 0.5)


@pytest.mark.parametrize("fmt", ["obj", "fbx", "dae"])
def test_export_formats(tmp_path, fmt):
    h = mhcore.new_human()
    h.set_gender(0.8).set_age(0.5)
    out = os.path.join(tmp_path, f"c.{fmt}")
    h.export(out)
    assert os.path.getsize(out) > 1000


def test_asset_discovery(human):
    for kind in ("clothes", "hair", "eyes", "skins"):
        assert isinstance(human.list_available(kind), list)


def test_equip_and_export(tmp_path):
    h = mhcore.new_human()
    clothes = h.list_available("clothes")
    if not clothes:
        pytest.skip("no clothes bundled")
    h.equip_clothes(clothes[0])
    out = os.path.join(tmp_path, "dressed.obj")
    h.export(out)
    groups = [l.split()[1] for l in open(out) if l.startswith("g ")]
    assert len(groups) >= 2  # body + at least one proxy


def _y_extent(coords):
    return float(coords[:, 1].max() - coords[:, 1].min())


def test_clothes_fit_child_body():
    """Clothes proxies must shrink with the body, not stay at adult authored size."""
    h = mhcore.new_human()
    clothes = h.list_available("clothes")
    if not clothes:
        pytest.skip("no clothes bundled")
    h.set_age(0.2).set_height(0.3)
    h.equip_clothes(clothes[0])
    body_ymax = float(h.human.meshData.coord[:, 1].max())
    pxy = next(iter(h.human.clothesProxies.values()))
    cloth_ymax = float(pxy.object.mesh.coord[:, 1].max())
    assert cloth_ymax <= body_ymax + 0.3, (
        "clothes still adult-sized: body_ymax=%.3f clothes_ymax=%.3f"
        % (body_ymax, cloth_ymax))


def test_unequip_clothes_and_hair():
    h = mhcore.new_human()
    clothes = h.list_available("clothes")
    if not clothes:
        pytest.skip("no clothes bundled")

    h.equip_clothes(clothes[0])
    assert h.get_equipped_clothes()
    assert h.unequip_clothes(clothes[0]) is True
    assert h.get_equipped_clothes() == []
    assert h.unequip_clothes(clothes[0]) is False

    h.equip_clothes(clothes[0])
    if len(clothes) > 1:
        h.equip_clothes(clothes[1])
    h.unequip_all_clothes()
    assert h.get_equipped_clothes() == []

    hair = h.list_available("hair")
    if hair:
        h.equip_hair(hair[0])
        assert h.human.hairProxy is not None
        h.unequip_hair()
        assert h.human.hairProxy is None


def test_fbx_export_keeps_bone_lengths():
    """FBX config must not inflate bone translations into a star-burst."""
    from mhcore.export import _fbx_config
    import numpy as np
    h = mhcore.new_human()
    h.set_skeleton(mhcore.data_path("rigs/default.mhskel"))
    cfg = _fbx_config(h.human)
    assert abs(cfg.scale - 10.0) < 1e-9
    skel = h.human.getSkeleton()
    if cfg.scale != 1:
        skel = skel.scaled(cfg.scale)
    lengths = [
        float(np.linalg.norm(
            b.getRelativeMatrix(cfg.meshOrientation, cfg.localBoneAxis, cfg.offset)[:3, 3]))
        for b in skel.getBones() if b.parent
    ]
    assert max(lengths) < 40.0, "bone local translation exploded: %s" % max(lengths)


def test_helper_bones_are_short_for_export():
    h = mhcore.new_human()
    h.set_skeleton(mhcore.data_path("rigs/default.mhskel"))
    import numpy as np
    long_helpers = []
    for b in h.human.getSkeleton().getBones():
        n = b.name.lower()
        if "oris" in n or "temporalis" in n or n.startswith("eye"):
            L = float(np.linalg.norm(b.tailPos - b.headPos))
            if L > 0.5:
                long_helpers.append((b.name, L))
    assert not long_helpers, "helper tails still long: %s" % long_helpers[:5]


def test_default_rig_follows_child_body():
    h = mhcore.new_human()
    h.set_age(0.2).set_height(0.3)
    h.set_skeleton(mhcore.data_path("rigs/default.mhskel"))
    skel = h.human.getSkeleton()
    head = skel.getBone("head")
    body_ymax = float(h.human.meshData.coord[:, 1].max())
    head_y = float(head.getRestTailPos()[1])
    assert abs(head_y - body_ymax) < 2.0, (
        "head bone y=%.3f vs mesh top=%.3f" % (head_y, body_ymax))


def test_set_pose_deforms_mesh():
    h = mhcore.new_human()
    poses = h.list_available("poses")
    tpose = next((p for p in poses if p.endswith("tpose.bvh")), None)
    if not tpose:
        pytest.skip("tpose.bvh not bundled")
    before = h.human.meshData.coord.copy()
    h.set_pose(tpose)
    after = h.human.meshData.coord
    assert not (before == after).all(), "applying tpose should skin the mesh"
    h.set_pose("")
    restored = h.human.meshData.coord
    assert (before == restored).all(), "clearing pose should restore rest mesh"


def test_set_expression_from_mhpose(tmp_path):
    h = mhcore.new_human()
    mhpose = os.path.join(tmp_path, "smile.mhpose")
    with open(mhpose, "w") as f:
        f.write('{"name":"smile","unit_poses":{"LeftCheekUp":1.0,"RightCheekUp":1.0}}')
    before = h.human.meshData.coord.copy()
    h.set_expression(mhpose)
    after = h.human.meshData.coord
    assert not (before == after).all(), "expression should move face verts"


def test_mhm_full_roundtrip(tmp_path):
    h = mhcore.new_human()
    h.set_gender(0.9).set_age(0.55).set_muscle(0.7)
    h.apply_modifier("head/head-oval", 0.4)
    h.set_skeleton(mhcore.data_path("rigs/default.mhskel"))
    for kind, equip in (("clothes", h.equip_clothes), ("hair", h.equip_hair),
                        ("eyes", h.equip_eyes)):
        avail = h.list_available(kind)
        if avail:
            equip(avail[0])
    skins = h.list_available("skins")
    if skins:
        h.set_skin(skins[0])

    a = h.save_mhm(os.path.join(tmp_path, "a.mhm"))
    h2 = mhcore.new_human()
    h2.load_mhm(a)
    b = h2.save_mhm(os.path.join(tmp_path, "b.mhm"))

    def norm(f):
        return sorted(l.strip() for l in open(f)
                      if l.strip() and not l.startswith(("camera", "#", "version")))

    assert norm(a) == norm(b)


# --------------------------------------------------------------------------
# Export verification: assert the *exported file*, not just the in-memory model.
# These target the four Blender symptoms the user reported.
# --------------------------------------------------------------------------

import re


def _read(path):
    with open(path) as f:
        return f.read()


def test_export_autorig_binds_and_metre_scale(tmp_path):
    """Default export (no explicit set_skeleton) must be skinned and metre-scaled."""
    h = mhcore.new_human()
    h.set_gender(1.0).set_age(0.5)
    dae = os.path.join(tmp_path, "a.dae")
    h.export(dae)  # defaults: rig="deform", metres

    s = _read(dae)
    # bound armature with skin weights (symptom: "no weights / not bound")
    assert s.count("<controller") >= 1
    assert s.count("<vertex_weights") >= 1
    assert 'type="JOINT"' in s
    # real-world unit (symptom: "model huge"): DAE declares 1 unit = 0.1 m, so a
    # ~17-unit (decimetre) human imports at ~1.7 m, not 17 m.
    m = re.search(r'<unit meter="([0-9.]+)"', s)
    assert m and abs(float(m.group(1)) - 0.1) < 1e-3
    # no face-muscle spikes (symptom: "face/eye bones as cones")
    assert not re.search(r'"(oris|levator|temporalis|oculi|risorius)', s)


def test_export_metre_scale_is_human_sized():
    h = mhcore.new_human()
    height_dm = float(h.human.meshData.coord[:, 1].max()
                      - h.human.meshData.coord[:, 1].min())
    assert 1.4 < height_dm * 0.1 < 2.1, "human should be ~1.7 m at metre scale"


def test_export_rig_none_is_unbound(tmp_path):
    h = mhcore.new_human()
    dae = os.path.join(tmp_path, "n.dae")
    h.export(dae, rig="none")
    assert "<controller" not in _read(dae)


def test_export_rig_full_keeps_face_bones(tmp_path):
    h = mhcore.new_human()
    dae = os.path.join(tmp_path, "f.dae")
    h.export(dae, rig="full")
    s = _read(dae)
    assert 'type="JOINT"' in s
    assert re.search(r"oris|levator|temporalis", s), "full rig keeps face muscles"


def test_fbx_deform_has_no_face_helpers(tmp_path):
    h = mhcore.new_human()
    h.set_gender(1.0).set_age(0.5)
    fbx = os.path.join(tmp_path, "d.fbx")
    h.export(fbx, format="fbx", rig="deform")
    data = open(fbx, "rb").read()
    for name in (b"tongue00", b"oris01", b"temporalis01", b"levator"):
        assert name not in data, name


def test_deform_rig_is_clean_and_fully_skinned():
    from mhcore import assets
    h = mhcore.new_human()
    h.set_age(0.3)
    d = assets.build_deform_skeleton(h.human)
    names = [b.name for b in d.getBones()]
    assert names, "deform rig has bones"
    assert not any(assets._is_face_muscle(n) for n in names), "no face-muscle bones"
    assert not any("tongue" in n.lower() or n.lower() == "jaw" for n in names)
    vw = d.getVertexWeights()
    assert vw is not None and len(vw.data) == len(names), "every deform bone is weighted"


def test_export_bound_after_morph_then_rig(tmp_path):
    """Morphing after set_skeleton must still export a bound, body-sized rig."""
    h = mhcore.new_human()
    h.set_skeleton(mhcore.data_path("rigs/default.mhskel"))
    h.set_age(0.2).set_height(0.2)  # shrink AFTER rigging
    dae = os.path.join(tmp_path, "m.dae")
    h.export(dae, rig="full")
    s = _read(dae)
    assert s.count("<controller") >= 1 and "<vertex_weights" in s
