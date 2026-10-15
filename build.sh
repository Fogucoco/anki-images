#!/bin/bash
# SPDX-License-Identifier: GPL-3.0-or-later
set -euo pipefail
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"
if [ "$(uname -s)" != Darwin ] || [ "$(uname -m)" != arm64 ]; then
    echo 'Build on an Apple Silicon Mac with macOS 14 or later.' >&2
    exit 1
fi
if [ ! -x .venv/bin/python ]; then
    python3 -m venv .venv
fi
.venv/bin/python -m pip install -r requirements-build.txt
.venv/bin/python -m unittest discover -s tests
.venv/bin/python tools/collect_licenses.py
.venv/bin/python tools/build_assets.py
export PYINSTALLER_CONFIG_DIR="$PROJECT_DIR/work/pyinstaller-cache"
.venv/bin/python -m PyInstaller --noconfirm --distpath dist --workpath work/pyinstaller AnkiImages.spec
.venv/bin/python tools/package_dmg.py
