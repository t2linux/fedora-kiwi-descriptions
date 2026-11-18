# AGENTS.md — fedora-agentic

Guidance for contributors and AI agents working in this repository. It describes
what this project is, how images are built, and how to customize them. The
authoritative source of truth is the code in this repo — if you spot drift
between this file and the actual files here, trust the **code** and update this
file.

## What this project is

This repository builds a **mutable (traditional `dnf`-based) Fedora distro**
with an agentic layer on top. The stack, from bottom to top, is:

1. A KIWI NG-built Fedora base image (KDE Plasma desktop).
2. [llama.cpp](https://github.com/ggml-org/llama.cpp) running as a **systemd
   service** (`llama-server`) exposing an HTTP inference API on `127.0.0.1:8080`.
3. [pi-agent](https://github.com/earendil-works/pi-coding-agent) as the interface
   to `llama.cpp`.
4. A **custom KDE Plasma widget** as the GUI for `pi-agent`.

The base is a normal, fully-updatable Fedora image: it ships standard
`/etc/yum.repos.d/` files pointing at Fedora's official mirrors, so after
installation users run `sudo dnf upgrade` and receive updates straight from
Fedora's infrastructure — no custom update server is hosted.

## How ISOs are built

This repo follows the upstream
[fedora-kiwi-descriptions](https://github.com/t2linux/fedora-kiwi-descriptions)
layout and uses **KIWI NG** to build images. KIWI NG runs reliably inside
containers — it does **not** require hardware KVM or SELinux workarounds, which
is why Fedora's own Spin/Edition builds migrated to it (the older
`livemedia-creator` breaks frequently inside containers).

### Build environment

- ISOs are built and expected to run on the latest stable release of Fedora Linux.
- Install build dependencies:

  ```bash
  sudo dnf --assumeyes install kiwi kiwi-systemdeps distribution-gpg-keys git
  ```

- Build an image with the wrapper script (substitute `<image_type>` and
  `<image_profile>` from [`VARIANTS.md`](VARIANTS.md)):

  ```bash
  sudo ./kiwi-build \
      --kiwi-file=Fedora.kiwi \
      --image-type=<image_type> \
      --image-profile=<image_profile> \
      --image-release=0 \
      --output-dir=./outdir
  ```

### CI / GitHub Actions

GitHub runners run Ubuntu, so the build launches a **privileged**
`fedora:latest` container (KIWI needs loop devices and must build the squashfs
filesystem). The workflow lives in `.github/workflows/build.yml`.

It also runs a lightweight **config integrity** job (`validate-config`, no
privileged container needed) before the ISO build:

```bash
sudo apt-get update && sudo apt-get install -y python3-yaml
python3 scripts/check_file_integrity.py
```

[`scripts/check_file_integrity.py`](scripts/check_file_integrity.py) walks the
repo and confirms every configuration file is well-formed — XML/KIWI
(`.xml`, `.kiwi`) with the standard library, YAML (`.yaml`, `.yml`, `.fmf`)
with PyYAML, and TOML (`.toml`) with `tomllib`. Folders whose contents are a
single, extension-agnostic format are validated against that format no matter
the file name: today only the `tmt/` folder, where every FMF definition is
YAML even when a file is named e.g. `tiny-disk.xml`. It exits non-zero on any
parse error, so a corrupted or half-edited config fails CI before a broken
ISO is ever built. It runs on
pull requests targeting `main`, on pushes to `main`, and manually via
workflow dispatch — so every PR gets an ISO build before merge. The actual
GitHub Releases upload is gated behind `if: github.event_name == 'push'`, so a
release is published only on pushes to `main` and never from a pull request.

## Repository structure

```text
├── Fedora.kiwi            # Root image description; pulls in components + teams
├── config.sh              # Runs inside the image chroot after overlaying root/
├── kiwi-build             # Wrapper that calls `kiwi-ng` correctly
├── components/
│   ├── common.xml
│   ├── boot.xml
│   └── desktops/
│       └── kde.xml        # KDE profile package list (add/remove packages here)
├── repositories/          # RPM repositories (mirrors, RPM Fusion, COPRs)
├── teams/                 # Desktop-environment team/package groupings
└── root/                  # Overlay directory; files copied verbatim into the image
    └── etc/
        └── ...            # e.g. sysconfig, systemd unit files
```

## Customizing an image

There are two main areas to customize, both committed via the PR workflow:

### 1. Package lists

Edit Fedora's package XML — `components/desktops/kde.xml` (the KDE profile) and,
where relevant, `Fedora.kiwi`'s `<packages type="image">` block — to add or
remove RPM packages, group packages, and third-party repositories (RPM Fusion or
COPRs). To pull llama.cpp into the image:

```xml
<package name="llama-cpp"/>
```

For GPU-accelerated Vulkan builds, add a COPR repository instead of the default
CPU-focused package:

```xml
<repository type="rpm-md">https://copr.fedorainfracloud.org/coprs/sneed/llama-cpp-vulkan/repo/</repository>
```

### 2. System configs and scripts

- Place custom files (dotfiles, `/etc` tweaks) under `root/`; KIWI copies them
  into the image verbatim before running `config.sh`.
- Add post-install shell commands to `config.sh`, which runs inside the image
  chroot after `root/` is overlaid.

## The agentic stack in detail

### systemd service — `llama-server`

Unit file and environment go under `root/etc/systemd/system/` and
`root/etc/sysconfig/`, so both live users and installed systems get it out of
the box:

`root/etc/sysconfig/llama-server`:

```ini
LLAMA_MODEL="/var/lib/llama-cpp/models/default.gguf"
LLAMA_HOST="127.0.0.1"
LLAMA_PORT="8080"
LLAMA_ARGS="--ctx-size 4096"
```

`root/etc/systemd/system/llama-server.service`:

```ini
[Unit]
Description=llama.cpp HTTP Inference Server
After=network-online.target
Wants=network-online.target
# Don't fail on first boot before a model is placed there
ConditionPathExists=/var/lib/llama-cpp/models/default.gguf

[Service]
Type=simple
DynamicUser=yes
StateDirectory=llama-cpp
EnvironmentFile=-/etc/sysconfig/llama-server
ExecStart=/usr/bin/llama-server -m ${LLAMA_MODEL} --host ${LLAMA_HOST} --port ${LLAMA_PORT} ${LLAMA_ARGS}
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Notes:

- `StateDirectory=llama-cpp` auto-creates `/var/lib/llama-cpp` with proper
  permissions for `DynamicUser=yes`.
- No `.gguf` model ships in the ISO (keeps it small); users download one into
  `/var/lib/llama-cpp/models/`. The `ConditionPathExists` guard prevents the
  service from failing on first boot.

### KDE Plasma widgets

Install widgets system-wide with `kpackagetool6 -g` so they land in
`/usr/share/plasma/plasmoids/` and are available to the live user and to any
account created during installation. Put widget archives under `root/tmp/widgets/`
and install them in `config.sh`:

```bash
# 1. Create the model directory for llama.cpp
mkdir -p /var/lib/llama-cpp/models

# 2. Enable the llama-server systemd service
systemctl enable llama-server.service

# 3. Install custom KDE Plasma widgets system-wide
if [ -d /tmp/widgets ]; then
    for widget in /tmp/widgets/*.plasmoid; do
        [ -e "$widget" ] || continue
        kpackagetool6 --global --type Plasma/Applet --install "$widget"
    done
    rm -rf /tmp/widgets
fi
```

## Keeping the ISO under 2 GB

GitHub Releases caps uploads at 2 GB per file. A default Fedora KDE live ISO
exceeds this (≈2.5+ GB), so:

- Strip heavy default apps (e.g. `libreoffice-*`, `kdepim-addons`, `kmail`,
  `kontact`, `dragon`, `elisa-player`, `akregator`, `gwenview`) from the KDE
  profile so users can install them later via `dnf` or Flatpak.
- Swap `fedora-logos` for `generic-logos` (and `fedora-release` for
  `generic-release` if needed) to comply with Fedora's remix/branding rules when
  redistributing a modified ISO publicly.
- Fail the CI build if the ISO ever exceeds GitHub's limit — add a check in
  `.github/workflows/build.yml` after `./kiwi-build`:

  ```bash
  ISO_FILE=$(find ./outdir -name "*.iso" | head -n 1)
  ISO_SIZE=$(stat -c%s "$ISO_FILE")
  echo "Built ISO size: $((ISO_SIZE / 1024 / 1024)) MB"
  if [ "$ISO_SIZE" -ge 2147483648 ]; then
    echo "Error: ISO exceeds GitHub Releases 2GB limit!"
    exit 1
  fi
  ```

## Contribution workflow

- All changes are made via the **PR workflow** — never by committing directly to
  `main` or a release branch.
- Keep each PR focused on a single concern.
- When adding or removing a Zuul CI plan, regenerate the config:

  ```bash
  make generate-zuul-config
  ```

## References

- KIWI NG documentation: https://osinside.github.io/kiwi/
- Upstream image descriptions: t2linux/fedora-kiwi-descriptions
- Fedora package for llama.cpp: packages.fedoraproject.org/pkgs/llama-cpp/
- Remix branding rules: Fedora Remix documentation
