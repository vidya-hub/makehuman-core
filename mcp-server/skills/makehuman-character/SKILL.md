---
name: makehuman-character
description: Create, configure, save and export 3D human characters from a natural-language description. Use when the user asks to build/generate a MakeHuman character, adjust body properties (gender, age, weight, muscle, height), dress a character, or save/export a .mhm/OBJ/FBX model. Requires the MakeHuman MCP server (in-process mhcore by default; no running MakeHuman app).
---

# MakeHuman character builder

Build MakeHuman characters through the `makehuman` MCP server. The default
`local` backend runs `mhcore` in-process — no MakeHuman GUI, no Qt, no OpenGL.
A `socket` backend can drive a running MakeHuman if the user asks for it.

## Before you start

1. Call `ping`. On the local backend this should return OK immediately.
2. If ping says `NOT READY` and mentions the socket, the user is on the socket
   backend: tell them to launch MakeHuman and tick **Accept connections** on
   the Socket task, or switch to `MAKEHUMAN_BACKEND=local`.
   Do not proceed until `ping` returns OK.

## Canonical workflow

Follow this order — macros first (they drive many targets), then details,
then assets, then persist:

1. **Body macros** — `set_gender`, `set_age`, `set_weight`, `set_muscle`,
   `set_height`. All take a float **0.0–1.0**.
2. **Detail modifiers** (optional) — call `list_modifiers` to discover names,
   then `apply_modifier(modifier, power)`. `power` is 0.0–1.0, or **-1.0..1.0**
   for two-sided (symmetric) modifiers such as `*-scale-horiz`, `*-trans-*`.
3. **Assets** (optional) — discover with `list_available_*`, then `equip_*` /
   `set_skin`. Asset lists are **machine-specific** (they depend on what is
   installed), so always list before equipping; never guess a path.
4. **Pose / expression** (optional) — `list_available_poses` then `set_pose`.
   Expressions are `.mhpose` files (`list_available_expressions`; the bundle
   may ship none). Pose and expression are local-backend only.
5. **Persist** — `save_character(path)` writes a native `.mhm` (captures
   everything: modifiers, materials, skeleton, equipped assets, pose). Optionally
   `export_character(path, format)` for `obj` | `fbx` | `dae` (`mhx2` is
   socket-backend only).

Use `new_character` to discard the current human and start over.

## Value model

Macro and most modifier values are normalized 0.0–1.0. Meaning of the macro
extremes:

| Macro     | 0.0            | 0.5            | 1.0            |
|-----------|----------------|----------------|----------------|
| gender    | fully female   | androgynous    | fully male     |
| age       | 1 year         | 25 years       | 90 years       |
| weight    | thin/minimum   | average        | heavy/maximum  |
| muscle    | untoned        | average        | very muscular  |
| height    | shortest       | average        | tallest        |

(Age is non-linear below 0.5: ~0.1875 ≈ 10 years, 0.5 ≈ 25 years.)

## Recipes (starting points — adjust to the request)

- **Adult athletic male**: gender 1.0, age 0.5, weight 0.5, muscle 0.8, height 0.7
- **Elderly slim female**: gender 0.0, age 0.9, weight 0.35, muscle 0.35, height 0.45
- **Young average child**: age ~0.19, gender per request, weight 0.5, muscle 0.5
- **Heavyset middle-aged man**: gender 1.0, age 0.65, weight 0.85, muscle 0.45

## Tips

- Confirm the target save path with the user; pass an absolute path to
  `save_character` (a `.mhm` extension is added if omitted).
- If a tool returns a string starting with `ERROR`, relay it and stop — do not
  retry blindly. `ERROR (not connected)` / `NOT READY` means the socket backend
  cannot reach MakeHuman.
- Report what you set (the macro values and equipped assets) so the user can
  fine-tune.
