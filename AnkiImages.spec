# PyInstaller specification for a standalone, ad-hoc-signed macOS application.
from pathlib import Path

root = Path(SPECPATH)
analysis = Analysis(
    [str(root / 'app.py')], pathex=[str(root)], binaries=[], datas=[(str(root / 'LICENSE'), 'licenses'), (str(root / 'README.md'), 'Documentation'), (str(root / 'assets' / 'app-icon.png'), 'assets'), (str(root / 'work' / 'third-party-licenses'), 'licenses/third-party')],
    hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[],
    noarchive=False,
)
archive = PYZ(analysis.pure)
executable = EXE(
    archive, analysis.scripts, [], exclude_binaries=True, name='Anki Images',
    debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
    console=False, target_arch='arm64', codesign_identity=None, entitlements_file=None,
)
collection = COLLECT(executable, analysis.binaries, analysis.datas, strip=False,
                     upx=False, name='Anki Images')
app = BUNDLE(collection, name='Anki Images.app', icon=str(root / 'work' / 'app-icon.icns'),
    bundle_identifier='io.github.fogucoco.ankiimages',
    info_plist={'CFBundleShortVersionString': '1.0.0', 'CFBundleVersion': '1',
                'CFBundleDevelopmentRegion': 'en', 'CFBundleLocalizations': ['en', 'ru'],
                'NSHighResolutionCapable': True})
