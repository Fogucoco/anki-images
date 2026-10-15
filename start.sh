#!/bin/bash
# SPDX-License-Identifier: GPL-3.0-or-later
set -euo pipefail
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"
if [ "$#" -ne 0 ]; then
    echo 'This is a desktop application. Run ./start.sh without arguments.' >&2
    exit 2
fi
if [ ! -x .venv/bin/python ]; then
    python3 -m venv .venv
fi
if [ ! -f .venv/requirements.installed ] || ! cmp -s requirements.txt .venv/requirements.installed; then
    .venv/bin/python -m pip install -r requirements.txt
    cp requirements.txt .venv/requirements.installed
fi
exec .venv/bin/python app.py
