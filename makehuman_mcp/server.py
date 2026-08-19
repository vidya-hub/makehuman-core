"""FastMCP server exposing MakeHuman character-creation tools.

Tools run against a backend (see makehuman_mcp.backends):

- ``local`` (default): the GUI-free ``mhcore`` library in-process. No running
  MakeHuman required.
- ``socket``: a running MakeHuman GUI over its socket bridge.

Environment variables:
    MAKEHUMAN_BACKEND  local | socket   (default: local if mhcore installed)
    MAKEHUMAN_HOST     socket backend host (default 127.0.0.1)
    MAKEHUMAN_PORT     socket backend port (default 12345)
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .backends import BackendError, make_backend
from .client import MakeHumanConnectionError, MakeHumanError

mcp = FastMCP("makehuman")

_backend = None


def _b():
    global _backend
    if _backend is None:
        _backend = make_backend()
    return _backend


def _safe(fn):
    """Run a backend call, turning errors into readable tool output."""
    try:
        result = fn()
    except MakeHumanConnectionError as exc:
        return f"ERROR (not connected): {exc}"
    except (MakeHumanError, BackendError) as exc:
        return f"ERROR: {exc}"
    except Exception as exc:  # surface anything else cleanly to the model
        return f"ERROR: {type(exc).__name__}: {exc}"
    return result if isinstance(result, str) else str(result)


# --------------------------------------------------------------------------
# Status
# --------------------------------------------------------------------------

@mcp.tool()
def ping() -> str:
    """Check the backend is ready. Call this first.

    With the default in-process backend this always works. With the socket
    backend it fails unless MakeHuman is running with the socket enabled.
    """
    try:
        return _b().ping()
    except (MakeHumanConnectionError, MakeHumanError, BackendError) as exc:
        return f"NOT READY: {exc}"


@mcp.tool()
def new_character() -> str:
    """Discard the current character and start a fresh base human."""
    return _safe(lambda: _b().reset() if hasattr(_b(), "reset")
                 else "ERROR: backend has no reset (socket backend is stateful in the GUI).")


# --------------------------------------------------------------------------
# Body macros (0.0 - 1.0)
# --------------------------------------------------------------------------

@mcp.tool()
def set_gender(value: float) -> str:
    """Set gender. 0.0 = fully female, 0.5 = androgynous, 1.0 = fully male."""
    return _safe(lambda: _b().set_macro("gender", value))


@mcp.tool()
def set_age(value: float) -> str:
    """Set age. 0.0 = 1 year, 0.1875 = 10 years, 0.5 = 25 years, 1.0 = 90 years."""
    return _safe(lambda: _b().set_macro("age", value))


@mcp.tool()
def set_weight(value: float) -> str:
    """Set weight/body mass. 0.0 = thin, 0.5 = average, 1.0 = heavy."""
    return _safe(lambda: _b().set_macro("weight", value))


@mcp.tool()
def set_muscle(value: float) -> str:
    """Set muscle tone. 0.0 = untoned, 0.5 = average, 1.0 = very muscular."""
    return _safe(lambda: _b().set_macro("muscle", value))


@mcp.tool()
def set_height(value: float) -> str:
    """Set height. 0.0 = shortest, 0.5 = average, 1.0 = tallest."""
    return _safe(lambda: _b().set_macro("height", value))


# --------------------------------------------------------------------------
# Detail modifiers
# --------------------------------------------------------------------------

@mcp.tool()
def list_modifiers() -> str:
    """List every available modifier name (e.g. 'head/head-oval').

    Use this to discover fine-grained controls before calling apply_modifier.
    """
    return _safe(lambda: _b().list_modifiers())


@mcp.tool()
def apply_modifier(modifier: str, power: float) -> str:
    """Apply a detail modifier by full name.

    'power' is 0.0-1.0 for one-sided modifiers, or -1.0..1.0 for two-sided
    (symmetric) ones such as 'head/head-scale-horiz'.
    """
    return _safe(lambda: _b().apply_modifier(modifier, power))


@mcp.tool()
def get_applied_targets() -> str:
    """Return the morph targets currently applied to the character, with weights."""
    return _safe(lambda: _b().get_applied_targets())


# --------------------------------------------------------------------------
# Assets: discovery
# --------------------------------------------------------------------------

@mcp.tool()
def list_available_clothes() -> str:
    """List paths to all installed clothes assets (.mhclo files)."""
    return _safe(lambda: _b().list_available("clothes"))


@mcp.tool()
def list_available_hair() -> str:
    """List paths to all installed hair assets (.mhclo files)."""
    return _safe(lambda: _b().list_available("hair"))


@mcp.tool()
def list_available_skins() -> str:
    """List paths to all installed skin materials (.mhmat files)."""
    return _safe(lambda: _b().list_available("skins"))


@mcp.tool()
def list_available_eyebrows() -> str:
    """List paths to all installed eyebrow assets (.mhclo files)."""
    return _safe(lambda: _b().list_available("eyebrows"))


@mcp.tool()
def list_available_eyelashes() -> str:
    """List paths to all installed eyelash assets (.mhclo files)."""
    return _safe(lambda: _b().list_available("eyelashes"))


@mcp.tool()
def list_available_poses() -> str:
    """List paths to bundled pose BVH files (e.g. tpose)."""
    return _safe(lambda: _b().list_available("poses"))


@mcp.tool()
def list_available_expressions() -> str:
    """List paths to installed facial expression .mhpose files (may be empty)."""
    return _safe(lambda: _b().list_available("expressions"))


@mcp.tool()
def list_available_rigs() -> str:
    """List paths to bundled skeleton .mhskel files (usually just default)."""
    return _safe(lambda: _b().list_available("rigs"))


# --------------------------------------------------------------------------
# Assets: equip / unequip. 'path' comes from a list_available_* call.
# --------------------------------------------------------------------------

@mcp.tool()
def equip_clothes(path: str) -> str:
    """Equip a clothing item by its .mhclo path. Multiple items can be equipped."""
    return _safe(lambda: _b().equip("clothes", path))


@mcp.tool()
def unequip_clothes(path: str) -> str:
    """Unequip a single clothing item by its .mhclo path."""
    return _safe(lambda: _b().unequip_clothes(path))


@mcp.tool()
def unequip_all_clothes() -> str:
    """Remove all currently equipped clothing."""
    return _safe(lambda: _b().unequip_all_clothes())


@mcp.tool()
def equip_hair(path: str) -> str:
    """Set the hair by its .mhclo path (replaces any current hair)."""
    return _safe(lambda: _b().equip("hair", path))


@mcp.tool()
def equip_eyebrows(path: str) -> str:
    """Set the eyebrows by their .mhclo path."""
    return _safe(lambda: _b().equip("eyebrows", path))


@mcp.tool()
def equip_eyelashes(path: str) -> str:
    """Set the eyelashes by their .mhclo path."""
    return _safe(lambda: _b().equip("eyelashes", path))


@mcp.tool()
def set_skin(path: str) -> str:
    """Set the body skin material by its .mhmat path (from list_available_skins)."""
    return _safe(lambda: _b().set_skin(path))


@mcp.tool()
def get_equipped_clothes() -> str:
    """List the .mhclo paths of currently equipped clothing."""
    return _safe(lambda: _b().get_equipped_clothes())


@mcp.tool()
def set_pose(path: str) -> str:
    """Apply a body pose from a .bvh (or .mhp) path. Local backend only.

    Use list_available_poses to discover bundled poses such as tpose.
    Pass an empty path to clear the pose.
    """
    return _safe(lambda: _b().set_pose(path))


@mcp.tool()
def set_skeleton(path: str) -> str:
    """Set the export skeleton from a .mhskel path (from list_available_rigs).

    Always do this after macros/clothes, before export. Use the bundled
    default.mhskel. Posing uses the internal base rig; this one is for FBX/DAE.
    """
    return _safe(lambda: _b().set_skeleton(path))


@mcp.tool()
def set_expression(path: str) -> str:
    """Apply a facial expression from a .mhpose file. Local backend only.

    Blends onto the current body pose. Pass an empty path to clear it.
    """
    return _safe(lambda: _b().set_expression(path))


# --------------------------------------------------------------------------
# Persist and export
# --------------------------------------------------------------------------

@mcp.tool()
def save_character(path: str) -> str:
    """Save the current character as a native MakeHuman .mhm file.

    Captures modifiers, materials, skeleton and equipped assets. A '.mhm'
    extension is added if missing.
    """
    return _safe(lambda: _b().save(path))


@mcp.tool()
def load_character(path: str) -> str:
    """Load a .mhm file, replacing the current character."""
    return _safe(lambda: _b().load(path))


@mcp.tool()
def export_character(path: str, format: str = "obj") -> str:
    """Export the current character mesh to a 3D file.

    'format' is one of: obj, fbx, dae (mhx2 requires the socket backend with the
    MHX2 plugin installed).
    """
    fmt = format.lower().strip()
    return _safe(lambda: _b().export(path, fmt))


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
