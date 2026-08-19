#!/usr/bin/env python3
"""Pack ./data into dist/mhcore-data-<ver>.tar.gz and a .sha256 sidecar."""

from __future__ import annotations

import hashlib
import os
import sys
import tarfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from mhcore.datapack import DATA_VERSION  # noqa: E402


def main() -> None:
    src = os.path.join(ROOT, "data")
    if not os.path.isdir(src):
        sys.exit("no data/ directory at %s" % src)
    out_dir = os.path.join(ROOT, "dist")
    os.makedirs(out_dir, exist_ok=True)
    name = "mhcore-data-%s.tar.gz" % DATA_VERSION
    dest = os.path.join(out_dir, name)

    print("writing", dest)
    with tarfile.open(dest, "w:gz") as tar:
        tar.add(src, arcname="data")

    sha = hashlib.sha256()
    with open(dest, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            sha.update(chunk)
    digest = sha.hexdigest()
    sidecar = dest + ".sha256"
    with open(sidecar, "w") as fh:
        fh.write("%s  %s\n" % (digest, name))
    print(digest, name)
    print("wrote", sidecar)


if __name__ == "__main__":
    main()
