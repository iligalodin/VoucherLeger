#!/usr/bin/env python3
"""Verify the Thunderstore archive has valid metadata and only release files."""

from __future__ import annotations

import json
import struct
import sys
import zipfile
from pathlib import Path

EXPECTED_FILES = (
    "CHANGELOG.md",
    "README.md",
    "VoucherLedger.json",
    "VoucherLedger.lua",
    "icon.png",
    "lovely.toml",
    "manifest.json",
    "assets/1x/icon.png",
    "assets/2x/icon.png",
)
REQUIRED_MANIFEST_FIELDS = {"name", "version_number", "website_url", "description", "dependencies"}


def png_dimensions(data: bytes) -> tuple[int, int]:
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError("icon.png is not a PNG")
    return struct.unpack(">II", data[16:24])


def main(project_dir: Path, supplied_archive: str | None) -> None:
    manifest_path = project_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    archive = Path(supplied_archive) if supplied_archive else project_dir / "dist" / f"VoucherLedger-{manifest['version_number']}.zip"

    with zipfile.ZipFile(archive) as package:
        names = tuple(package.namelist())
        if names != EXPECTED_FILES:
            raise ValueError(f"Unexpected package layout: {names!r}")
        packaged_manifest = json.loads(package.read("manifest.json"))
        packaged_mod = json.loads(package.read("VoucherLedger.json"))
        if set(packaged_manifest) != REQUIRED_MANIFEST_FIELDS:
            raise ValueError("manifest.json has missing or unknown fields")
        if packaged_manifest["name"] != "VoucherLedger":
            raise ValueError("manifest.json has the wrong package name")
        if packaged_manifest["version_number"] != packaged_mod["version"]:
            raise ValueError("manifest and mod versions differ")
        if packaged_mod.get("icon_path") != "icon.png":
            raise ValueError("VoucherLedger.json must reference the packaged icon.png")
        if len(packaged_manifest["description"]) > 250:
            raise ValueError("manifest description exceeds 250 characters")
        if png_dimensions(package.read("icon.png")) != (256, 256):
            raise ValueError("icon.png must be 256x256")
        if png_dimensions(package.read("assets/1x/icon.png")) != (68, 68):
            raise ValueError("assets/1x/icon.png must be 68x68")
        if png_dimensions(package.read("assets/2x/icon.png")) != (136, 136):
            raise ValueError("assets/2x/icon.png must be 136x136")

    print(f"Validated {archive}")


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve(), sys.argv[2] if len(sys.argv) > 2 else None)
