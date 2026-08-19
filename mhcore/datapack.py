"""Locate or download the MakeHuman runtime data pack.

A git clone already has ``data/`` next to this package. A wheel/uvx install
does not — the pack is fetched once from GitHub Releases into the user cache.
"""

from __future__ import annotations

import hashlib
import os
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request

DATA_VERSION = "0.1.0"
_REPO = "vidya-hub/makehuman-core"
_ASSET = "mhcore-data-%s.tar.gz" % DATA_VERSION
_URL = "https://github.com/%s/releases/download/v%s/%s" % (_REPO, DATA_VERSION, _ASSET)
_SHA_URL = _URL + ".sha256"

_MARKER = ".complete"
_PROBE = os.path.join("3dobjs", "base.obj")


def cache_home() -> str:
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~/.cache")
    else:
        base = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache")
    return os.path.join(base, "mhcore")


def _has_data(root: str) -> bool:
    return os.path.isfile(os.path.join(root, "data", _PROBE))


def _root_from_data_dir(data_dir: str) -> str:
    """Accept either ``.../data`` or the parent that contains ``data/``."""
    data_dir = os.path.abspath(data_dir)
    if os.path.isfile(os.path.join(data_dir, _PROBE)):
        return os.path.dirname(data_dir)
    if os.path.isfile(os.path.join(data_dir, "data", _PROBE)):
        return data_dir
    raise RuntimeError(
        "MHCORE_DATA=%r does not contain 3dobjs/base.obj" % data_dir)


def resolve_data_root(clone_root: str) -> str:
    """Return the directory that contains ``data/`` (MakeHuman sys path)."""
    env = os.environ.get("MHCORE_DATA", "").strip()
    if env:
        return _root_from_data_dir(env)
    if _has_data(clone_root):
        return clone_root
    return _ensure_cached()


def _ensure_cached() -> str:
    dest = os.path.join(cache_home(), DATA_VERSION)
    if os.path.isfile(os.path.join(dest, _MARKER)) and _has_data(dest):
        return dest
    _download_and_extract(dest)
    return dest


def _log(msg: str) -> None:
    sys.stderr.write(msg + "\n")
    sys.stderr.flush()


def _fetch_sha256() -> str | None:
    try:
        with urllib.request.urlopen(_SHA_URL, timeout=30) as resp:
            text = resp.read().decode("ascii", errors="ignore").strip()
    except (urllib.error.URLError, TimeoutError, OSError):
        return None
    if not text:
        return None
    return text.split()[0]


def _download_and_extract(dest: str) -> None:
    os.makedirs(dest, exist_ok=True)
    expected = _fetch_sha256()
    _log("Downloading MakeHuman data (%s) to %s ..." % (_ASSET, dest))
    _log("This is a one-time ~430 MB download.")
    try:
        req = urllib.request.Request(_URL, headers={"User-Agent": "mhcore/" + DATA_VERSION})
        with urllib.request.urlopen(req, timeout=60) as resp:
            total = int(resp.headers.get("Content-Length") or 0)
            sha = hashlib.sha256()
            downloaded = 0
            fd, tmp = tempfile.mkstemp(prefix="mhcore-data-", suffix=".tar.gz")
            try:
                with os.fdopen(fd, "wb") as out:
                    while True:
                        chunk = resp.read(1024 * 1024)
                        if not chunk:
                            break
                        out.write(chunk)
                        sha.update(chunk)
                        downloaded += len(chunk)
                        if total:
                            pct = 100.0 * downloaded / total
                            _log("  %d / %d MB (%.0f%%)" % (
                                downloaded // (1024 * 1024),
                                total // (1024 * 1024), pct))
                digest = sha.hexdigest()
                if expected and digest != expected:
                    raise RuntimeError(
                        "data pack sha256 mismatch: got %s expected %s" % (
                            digest, expected))
                _log("Extracting ...")
                with tarfile.open(tmp, "r:gz") as tar:
                    tar.extractall(dest)
            finally:
                try:
                    os.remove(tmp)
                except OSError:
                    pass
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            "Could not download %s (%s). "
            "Create GitHub release v%s with %s, or clone the repo "
            "and set MHCORE_DATA to its data/ folder." % (
                _URL, exc, DATA_VERSION, _ASSET)) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError("Could not download MakeHuman data: %s" % exc) from exc

    if not _has_data(dest):
        raise RuntimeError(
            "Data pack extracted to %s but data/3dobjs/base.obj is missing" % dest)
    with open(os.path.join(dest, _MARKER), "w") as fh:
        fh.write(DATA_VERSION + "\n")
    _log("MakeHuman data ready.")
