
# Fedora KIWI image descriptions

This project is used to manage the Fedora KIWI image descriptions used in composing Fedora release images.

The `rawhide` branch is used for Fedora Rawhide images and each release branch is used by that release.

All changes should be made via the PR workflow.

## Image variants

Please look at [`VARIANTS`](VARIANTS.md) for details on the available
configurations that can be built.

## Image build quickstart

This is generally tested and expected to run on the latest stable release of Fedora Linux.
Other distributions may work, but there are no guarantees.

Set up your development environment and run the image build (substitute `<image_type>` and `<image_profile>` for the appropriate settings):

```bash
# Install kiwi
[]$ sudo dnf --assumeyes install kiwi kiwi-systemdeps distribution-gpg-keys
# Run the image build
[]$ sudo ./kiwi-build --kiwi-file=Fedora.kiwi --image-type=<image_type> --image-profile=<image_profile> --output-dir ./outdir
```

## CI information

This project is tested using the [Software Factory Zuul CI instance](https://fedora.softwarefactory-project.io/zuul/project/pagure.io/fedora-kiwi-descriptions)
using the [Test Management Tool](https://tmt.readthedocs.io/).

The Zuul configuration is generated from the Jinja2 template `.zuul.yaml.j2`.
When adding or removing a tmt plan, please run the following command to regenerate the Zuul configuration:

```bash
[]$ make generate-zuul-config
```

## Config integrity check

[`scripts/check_file_integrity.py`](scripts/check_file_integrity.py) verifies
that every configuration file in the repo is well-formed — XML/KIWI
(`.xml`, `.kiwi`), YAML (`.yaml`, `.yml`, `.fmf`), and TOML (`.toml`). Folders whose contents are a single, extension-agnostic
format are validated against that format no matter the file name — right now
only the `tmt/` folder, where every FMF definition is YAML even when named
e.g. `tiny-disk.xml`. It is run automatically by GitHub Actions on every push
to `main` and pull request,
but you can also run it locally:

```bash
# Optional: install the YAML parser so `.yaml`/`.yml`/`.fmf` are checked
dnf install -y python3-yaml   # or: pip install pyyaml
python3 scripts/check_file_integrity.py
```

It exits non-zero if any file fails to parse, which catches corruption or a
malformed edit (for example a truncated `<package>` tag) before it reaches a
build.

## Licensing

This is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, under version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
