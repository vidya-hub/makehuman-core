#!/usr/bin/env python3
"""End-to-end example: build a character headlessly and export it.

Run from the repo root:  python examples/build_character.py
"""

import os

import mhcore


def main(outdir="out"):
    os.makedirs(outdir, exist_ok=True)

    h = mhcore.new_human()
    print(h)

    # Body macros.
    h.set_gender(1.0).set_age(0.5).set_weight(0.55).set_muscle(0.8).set_height(0.72)

    # A couple of detail modifiers.
    h.apply_modifier("head/head-oval", 0.4)
    h.apply_modifier("nose/nose-scale-vert-decr|incr", 0.3)

    # Rig + assets.
    h.set_skeleton(mhcore.data_path("rigs/default.mhskel"))
    clothes = h.list_available("clothes")
    hair = h.list_available("hair")
    eyes = h.list_available("eyes")
    skins = h.list_available("skins")
    if clothes:
        h.equip_clothes(clothes[0])
    if hair:
        h.equip_hair(hair[0])
    if eyes:
        h.equip_eyes(eyes[0])
    if skins:
        h.set_skin(skins[0])

    # Persist + export.
    mhm = h.save_mhm(os.path.join(outdir, "hero.mhm"))
    print("saved:", mhm)
    for fmt in ("obj", "fbx", "dae"):
        path = h.export(os.path.join(outdir, f"hero.{fmt}"))
        print(f"exported {fmt}:", path, f"({os.path.getsize(path)} bytes)")


if __name__ == "__main__":
    main()
