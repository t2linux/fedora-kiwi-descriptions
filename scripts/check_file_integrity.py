#!/usr/bin/env python3
"""Verify the integrity of repository configuration files.

This script walks the repository and confirms that every known
configuration file (XML, YAML, TOML) is *well-formed* — i.e. it parses
without errors according to its format. It catches accidental corruption
or malformed edits (for example a truncated ``<package>`` tag or a broken
YAML list) before such a change reaches the built ISO.

Supported formats
-----------------
* XML / KIWI (``.xml``, ``.kiwi``) — validated with the standard library
  ``xml.etree.ElementTree``; no third-party dependency is required.
* YAML (``.yaml``, ``.yml``, ``.fmf``) — validated with `PyYAML
  <https://pyyaml.org/>`_. ``.fmf`` files are tmt FMF definitions, which
  are themselves YAML, so they share the same validator.
* TOML (``.toml``) — validated with the standard library ``tomllib``
  (Python 3.11+).

The script validates everything it can and reports clearly what it had to
skip when an optional parser is not installed, so it also runs sensibly on
machines that lack PyYAML. In CI, install the optional parsers (see
``.github/workflows/build.yml``) so every format is actually checked.

Usage
-----
::

    python3 scripts/check_file_integrity.py [ROOT]

``ROOT`` defaults to the repository root (the parent of this script's
``scripts/`` directory). Exits ``0`` when all validated files are
well-formed and non-zero otherwise.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Extensions mapped to their parser name ("stdlib" needs no import).
VALIDATORS = {
    "xml": "xml",
    "kiwi": "xml",
    "yaml": "yaml",
    "yml": "yaml",
    "fmf": "yaml",
    "toml": "toml",
}


def load_xml(path: Path) -> None:
    """Parse an XML/KIWI file with the standard library."""
    import xml.etree.ElementTree as ET

    ET.parse(str(path))


def load_yaml(path: Path) -> None:
    """Parse a YAML file (including FMF definitions)."""
    import yaml

    text = path.read_text(encoding="utf-8")
    # ``safe_load_full`` (PyYAML >= 6) also rejects multiple documents and
    # duplicate keys, which is what we want for a strict integrity check.
    try:
        yaml.safe_load_full(text)
    except AttributeError:  # older PyYAML without the *full* helpers
        yaml.safe_load(text)


def load_toml(path: Path) -> None:
    """Parse a TOML file with the standard library."""
    import tomllib

    with path.open("rb") as handle:
        tomllib.load(handle)


PARSERS = {
    "xml": load_xml,
    "yaml": load_yaml,
    "toml": load_toml,
}


def main(argv: list[str]) -> int:
    root = Path(argv[1]).resolve() if len(argv) > 1 else Path(__file__).resolve().parent.parent

    # Which optional parsers are available in this Python?
    unavailable: dict[str, str] = {}
    for name in ("yaml", "toml"):
        try:
            __import__(name if name != "toml" else "tomllib")
        except ImportError:
            hint = (
                "dnf install -y python3-yaml"
                if name == "yaml"
                else "upgrade to Python 3.11+ (tomllib) or pip install tomli"
            )
            unavailable[name] = hint

    totals: dict[str, int] = {}
    skipped: list[str] = []
    failures: list[tuple[str, Exception]] = []
    checked = 0

    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        # Skip the version marker and anything in VCS / hidden build dirs.
        if path.name == "version":
            continue
        ext = path.suffix[1:].lower()
        parser_name = VALIDATORS.get(ext)
        if parser_name is None:
            continue

        if parser_name in unavailable:
            skipped.append(f"{parser_name} ({path})")
            totals.setdefault(parser_name, 0)
            continue

        totals[parser_name] = totals.get(parser_name, 0) + 1
        try:
            PARSERS[parser_name](path)
            checked += 1
        except Exception as exc:  # noqa: BLE001 - report any parse failure
            failures.append((str(path), exc))

    # Report.
    print(f"Checked {checked} file(s) in {root}")
    for name in ("xml", "yaml", "toml"):
        if totals.get(name):
            print(f"  {name:>4}: {totals[name]} validated")
    if skipped:
        print("\nSkipped (parser not installed):")
        for item in skipped:
            print(f"  - {item}")

    if unavailable:
        print("\nOptional parsers unavailable (use `--require` or install them):")
        for name, hint in unavailable.items():
            print(f"  - {name}: install with `{hint}`")

    if failures:
        print("\nValidation failed:")
        for path, exc in failures:
            print(f"  ✗ {path}: {exc}")
        return 1

    if skipped:
        print("\nAll parseable files are well-formed (some formats were skipped).")
    else:
        print("\nAll configuration files are well-formed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
