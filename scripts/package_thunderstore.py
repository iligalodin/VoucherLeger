#!/usr/bin/env python3
"""Build the root-layout ZIP required by Thunderstore."""

from __future__ import annotations

import json
import os
import subprocess
import struct
import sys
import tempfile
import time
import zipfile
from pathlib import Path

PACKAGE_FILES = (
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
SOURCE_ICON = "assets/1x/icon.png"
MIN_ZIP_TIMESTAMP = 315532800  # 1980-01-01; ZIP cannot represent earlier dates.


def zip_datetime() -> tuple[int, int, int, int, int, int]:
    epoch = max(int(os.environ.get("SOURCE_DATE_EPOCH", MIN_ZIP_TIMESTAMP)), MIN_ZIP_TIMESTAMP)
    return time.gmtime(epoch)[:6]


def png_dimensions(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    if header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError(f"Package icon is not a PNG: {path}")
    return struct.unpack(">II", header[16:24])


def build_package_icon(source: Path, destination: Path) -> None:
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-i",
                str(source),
                "-vf",
                "scale=256:256:flags=neighbor",
                "-frames:v",
                "1",
                "-update",
                "1",
                str(destination),
            ],
            check=True,
        )
    except FileNotFoundError:
        raise RuntimeError("ffmpeg is required to build the Thunderstore icon") from None
    except subprocess.CalledProcessError as error:
        raise RuntimeError(f"Could not build the Thunderstore icon: {error}") from error

    if png_dimensions(destination) != (256, 256):
        raise ValueError("Thunderstore icon must be 256x256")


def main(project_dir: Path) -> None:
    manifest = json.loads((project_dir / "manifest.json").read_text(encoding="utf-8"))
    version = manifest["version_number"]
    archive = project_dir / "dist" / f"VoucherLedger-{version}.zip"
    archive.parent.mkdir(exist_ok=True)

    source_icon = project_dir / SOURCE_ICON
    if not source_icon.is_file():
        raise FileNotFoundError(f"Required package file is missing: {SOURCE_ICON}")

    with tempfile.TemporaryDirectory() as temporary_directory:
        package_icon = Path(temporary_directory) / "icon.png"
        build_package_icon(source_icon, package_icon)

        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as package:
            for name in PACKAGE_FILES:
                source = package_icon if name == "icon.png" else project_dir / name
                if not source.is_file():
                    raise FileNotFoundError(f"Required package file is missing: {name}")
                entry = zipfile.ZipInfo(name, date_time=zip_datetime())
                entry.create_system = 3
                entry.external_attr = 0o100644 << 16
                package.writestr(entry, source.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

    print(archive)


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())
