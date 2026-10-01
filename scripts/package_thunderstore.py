#!/usr/bin/env python3
"""Build the root-layout ZIP required by Thunderstore."""

from __future__ import annotations

import json
import os
import sys
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
)
MIN_ZIP_TIMESTAMP = 315532800  # 1980-01-01; ZIP cannot represent earlier dates.


def zip_datetime() -> tuple[int, int, int, int, int, int]:
    epoch = max(int(os.environ.get("SOURCE_DATE_EPOCH", MIN_ZIP_TIMESTAMP)), MIN_ZIP_TIMESTAMP)
    return time.gmtime(epoch)[:6]


def main(project_dir: Path) -> None:
    manifest = json.loads((project_dir / "manifest.json").read_text(encoding="utf-8"))
    version = manifest["version_number"]
    archive = project_dir / "dist" / f"VoucherLedger-{version}.zip"
    archive.parent.mkdir(exist_ok=True)

    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as package:
        for name in PACKAGE_FILES:
            source = project_dir / name
            if not source.is_file():
                raise FileNotFoundError(f"Required package file is missing: {name}")
            entry = zipfile.ZipInfo(name, date_time=zip_datetime())
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            package.writestr(entry, source.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

    print(archive)


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())
