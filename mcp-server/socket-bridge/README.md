# Socket bridge (optional — for the `socket` backend only)

The MCP server's default `local` backend uses `mhcore` in-process and needs
**none** of this. You only need the socket bridge if you want the `socket`
backend, which drives a **running MakeHuman GUI** over TCP.

Stock MakeHuman ships a socket plugin (`plugins/8_server_socket`) built for the
Blender bridge. It exposes only a subset of operations. This folder contains the
extended version that adds the ops the MCP server needs: the body-macro setters
(`setGender`/`setAge`/…), asset equip/discovery, `.mhm` save/load, and export.

These files are kept here so the MakeHuman checkout stays untouched — install
them into your own MakeHuman only if you want the socket backend.

## Install (recommended: copy the files)

Copy the four files over your MakeHuman plugin directory:

```bash
cp -r 8_server_socket/* /path/to/makehuman/makehuman/plugins/8_server_socket/
```

This overwrites `__init__.py` and `modops.py` and adds `assetops.py` and
`fileops.py`. Copying whole files avoids line-ending issues (MakeHuman ships
CRLF files).

## Install (alternative: apply the patch)

From your MakeHuman code directory (`makehuman/makehuman`):

```bash
git apply /path/to/8_server_socket.patch
# or, on a plain checkout:
patch -p1 < /path/to/8_server_socket.patch
```

Note: MakeHuman's repo uses `core.autocrlf=true` (CRLF working tree). If `patch`
reports hunk failures on `__init__.py`/`modops.py`, use the copy method above —
it is byte-independent.

## After installing

1. Launch MakeHuman and open the **Socket** task (Community tab).
2. Tick **Accept connections** (default `127.0.0.1:12345`).
3. Run the MCP server with `MAKEHUMAN_BACKEND=socket`.

## Contents

- `8_server_socket/` — the four complete plugin files (drop-in).
- `8_server_socket.patch` — the same changes as a diff against stock MakeHuman.
