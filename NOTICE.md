# NOTICE

`makehuman-core` (the `mhcore` package) is a derivative work of **MakeHuman**,
the open-source 3D character creation software by the MakeHuman Team.

- Upstream project: http://www.makehumancommunity.org/
- Upstream code: https://github.com/makehumancommunity/makehuman

This repository vendors, unmodified, a subset of the MakeHuman source under
`_vendor/` and bundles the MakeHuman runtime data under `data/`. The `mhcore/`
package adds a headless (no Qt, no OpenGL) integration layer on top of that
vendored source so characters can be built, saved and exported programmatically.

## Licensing

- MakeHuman **code** is licensed under the GNU Affero General Public License
  v3 (AGPL-3.0). The vendored source and this derivative remain under AGPL-3.0;
  see `LICENSE`.
- MakeHuman **assets/data** (the contents of `data/`: meshes, targets,
  materials, clothes, etc.) are distributed by the MakeHuman Team under their
  own asset license (CC0 for most targets/meshes). See the upstream
  `LICENSE.ASSETS.md` for details:
  https://github.com/makehumancommunity/makehuman/blob/master/LICENSE.ASSETS.md

If you distribute this software or run it as a network service, your
obligations under the AGPL-3.0 apply.
