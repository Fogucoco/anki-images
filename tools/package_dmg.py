# SPDX-License-Identifier: GPL-3.0-or-later
"""Build a drag-to-install DMG with the app icon on its volume and local file."""
from pathlib import Path
import shutil
import time
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
destination = root / 'dist' / 'Anki Images.dmg'
with tempfile.TemporaryDirectory(prefix='dmg-', dir=root / 'work') as temporary:
    stage = Path(temporary) / 'Anki Images'
    stage.mkdir()
    shutil.copytree(root / 'dist' / 'Anki Images.app', stage / 'Anki Images.app', symlinks=True)
    (stage / 'Applications').symlink_to('/Applications')
    icon = root / 'work' / 'app-icon.icns'
    shutil.copyfile(icon, stage / '.VolumeIcon.icns')
    # Keep the installation window focused on the two drag-and-drop targets.
    from ds_store import DSStore
    with DSStore.open(str(stage / '.DS_Store'), 'w+') as store:
        store['.']['vSrn'] = ('long', 1)
        store['.']['icvl'] = ('type', b'icnv')
        store['.']['bwsp'] = {
            'ShowStatusBar': False, 'ShowToolbar': False, 'ShowSidebar': False,
            'ShowTabView': False, 'ContainerShowSidebar': False,
            'WindowBounds': '{{200, 160}, {600, 360}}',
        }
        store['.']['icvp'] = {
            'viewOptionsVersion': 1, 'backgroundType': 1,
            'backgroundColorRed': 1.0, 'backgroundColorGreen': 1.0,
            'backgroundColorBlue': 1.0, 'iconSize': 128.0, 'textSize': 14.0,
            'gridOffsetX': 0.0, 'gridOffsetY': 0.0, 'gridSpacing': 100.0,
            'arrangeBy': 'none', 'labelOnBottom': True, 'showIconPreview': True,
            'showItemInfo': False,
        }
        store['Anki Images.app']['Iloc'] = (155, 155)
        store['Applications']['Iloc'] = (445, 155)
    writable = Path(temporary) / 'writable.dmg'
    subprocess.run(['hdiutil', 'create', '-volname', 'Anki Images', '-srcfolder', str(stage),
                    '-fs', 'HFS+', '-format', 'UDRW', str(writable)], check=True)
    mount = Path(temporary) / 'mounted'
    mount.mkdir()
    subprocess.run(['hdiutil', 'attach', '-readwrite', '-nobrowse', '-noautoopen',
                    '-mountpoint', str(mount), str(writable)], check=True)
    try:
        subprocess.run(['SetFile', '-c', 'icnC', str(mount / '.VolumeIcon.icns')], check=True)
        subprocess.run(['SetFile', '-a', 'C', str(mount)], check=True)
    finally:
        for attempt in range(5):
            detached = subprocess.run(['hdiutil', 'detach', str(mount)])
            if detached.returncode == 0:
                break
            time.sleep(1)
        else:
            raise RuntimeError(f'Could not detach build volume: {mount}')
    image = Path(temporary) / 'Anki Images.dmg'
    subprocess.run(['hdiutil', 'convert', str(writable), '-format', 'UDZO',
                    '-o', str(image)], check=True)
    # The mounted-volume icon is embedded in the filesystem. The local DMG file
    # also gets a Finder icon; its resource fork may be lost over HTTP downloads.
    resource = Path(temporary) / 'file-icon.r'
    icon_hex = icon.read_bytes().hex()
    resource.write_text("data 'icns' (-16455) {\n" +
                        ''.join(f'    $"{icon_hex[offset:offset + 64]}"\n'
                                for offset in range(0, len(icon_hex), 64)) + "};\n")
    subprocess.run(['Rez', '-a', str(resource), '-o', str(image)], check=True)
    subprocess.run(['SetFile', '-a', 'C', str(image)], check=True)
    image.replace(destination)
print(f'Built: {destination}')
