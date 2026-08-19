# makehuman-core (`mhcore`)

A **GUI-free** (no Qt, no OpenGL) Python library for building
[MakeHuman](http://www.makehumancommunity.org/) characters programmatically:
set body properties, apply modifiers, equip clothes/hair/eyes/skin, and
save/export — from a script, a server, or CI, with no running MakeHuman app.

It works by vendoring the unmodified MakeHuman source (`_vendor/`) and driving
it through a small headless shim (`mhcore/`) that stubs the GUI/GL modules and
supplies a headless application object. The character/geometry pipeline in
MakeHuman is pure numpy, so nothing here needs a display or a GPU.

## Install

The repository bundles ~430 MB of MakeHuman runtime data, so use an editable
install from a clone (not a wheel):

```bash
git clone https://github.com/vidya-hub/makehuman-core.git
cd makehuman-core
python3 -m venv .venv
./.venv/bin/pip install -e .    # only dependency: numpy
```

## Usage

```python
import mhcore

h = mhcore.new_human()

# body macros (0.0 - 1.0)
h.set_gender(1.0).set_age(0.5).set_weight(0.6).set_muscle(0.8).set_height(0.7)

# fine detail modifiers
print(len(h.list_modifiers()))          # ~269 available
h.apply_modifier("head/head-oval", 0.4)

# assets (discover, then equip by path)
h.set_skeleton(mhcore.data_path("rigs/default.mhskel"))
h.equip_clothes(h.list_available("clothes")[0])
h.equip_hair(h.list_available("hair")[0])
h.equip_eyes(h.list_available("eyes")[0])
h.set_skin(h.list_available("skins")[0])

# save the native format and export meshes
h.save_mhm("out/hero.mhm")
h.export("out/hero.obj")                 # also .fbx, .dae
```

See `examples/build_character.py` for a runnable end-to-end script.

An MCP server that drives this library in-process (no running MakeHuman) lives
in [`mcp-server/`](mcp-server/). See that README to install and register it
with a client.

## API (`mhcore.MHHuman`)

| Area | Methods |
|------|---------|
| Macros | `set_gender/set_age/set_weight/set_muscle/set_height(0.0–1.0)` |
| Modifiers | `list_modifiers()`, `apply_modifier(name, power)`, `get_applied_targets()` |
| Assets | `list_available(kind)`, `equip_clothes/equip_hair/equip_eyes/equip_eyebrows/equip_eyelashes/equip_teeth/equip_tongue(path)`, `unequip_clothes/unequip_all_clothes/unequip_hair`, `set_skin(path)` |
| Rig/pose | `set_skeleton(path)`, `set_pose(bvh)`, `set_expression(mhpose)` |
| Persist | `save_mhm(path)`, `load_mhm(path)` |
| Export | `export(path, format=None)` — `obj` \| `fbx` \| `dae` |

`kind` for `list_available`: `clothes`, `hair`, `eyes`, `eyebrows`,
`eyelashes`, `teeth`, `tongue`, `skins`, `poses`, `expressions`.

## Status / limitations

- Full `.mhm` round-trip: modifiers, skeleton, proxies (clothes/hair/eyes/…),
  skin + per-proxy materials all save and reload faithfully.
- Export: OBJ, FBX, DAE.
- `set_pose` applies a `.bvh` (or `.mhp`) to the base skeleton and skins the
  mesh. `set_expression` blends a `.mhpose` onto the face bones. Both are
  written into the `.mhm` and re-applied on load.
- Skin **textures** are referenced by path in exports; the library never loads
  pixel data (that path is the only Qt dependency and is intentionally avoided).

## License

AGPL-3.0-or-later. This is a derivative of MakeHuman; see `LICENSE` and
`NOTICE.md` for attribution and asset licensing.
