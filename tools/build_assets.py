# SPDX-License-Identifier: GPL-3.0-or-later
"""Convert the approved PNG icon into all native macOS icon representations."""
import subprocess
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage

root = Path(__file__).resolve().parents[1]
iconset = root / 'work' / 'app.iconset'
iconset.mkdir(parents=True, exist_ok=True)
image = QImage(str(root / 'assets' / 'app-icon.png'))
if image.isNull() or image.width() != image.height() or not image.hasAlphaChannel():
    raise ValueError('App icon must be a square PNG with an alpha channel.')
for size in (16, 32, 128, 256, 512):
    for scale in (1, 2):
        suffix = '@2x' if scale == 2 else ''
        target = iconset / f'icon_{size}x{size}{suffix}.png'
        scaled = image.scaled(size * scale, size * scale,
                              Qt.AspectRatioMode.KeepAspectRatio,
                              Qt.TransformationMode.SmoothTransformation)
        if not scaled.save(str(target)):
            raise OSError(f'Could not write {target}')
subprocess.run(['iconutil', '--convert', 'icns', '--output',
                str(root / 'work' / 'app-icon.icns'), str(iconset)], check=True)
