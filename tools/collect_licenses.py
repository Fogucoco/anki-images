# SPDX-License-Identifier: GPL-3.0-or-later
"""Collect runtime dependency notices and available license texts for packaging."""
from importlib.metadata import distribution
from pathlib import Path
import shutil

from packaging.requirements import Requirement

root = Path(__file__).resolve().parents[1]
output = root / 'work' / 'third-party-licenses'
output.mkdir(parents=True, exist_ok=True)
pending = [Requirement(line).name for line in (root / 'requirements.txt').read_text().splitlines()
           if line.strip() and not line.startswith('#')]
seen = set()
notices = ['# Bundled dependency notices', '', 'Application source: https://github.com/Fogucoco/anki-images', '']
while pending:
    name = pending.pop()
    package = distribution(name)
    canonical = package.metadata['Name']
    if canonical.lower() in seen:
        continue
    seen.add(canonical.lower())
    license_name = package.metadata.get('License-Expression') or package.metadata.get('License') or 'See project license'
    urls = package.metadata.get_all('Project-URL') or []
    homepage = package.metadata.get('Home-page')
    notices.extend([f'## {canonical} {package.version}', license_name, *urls, homepage or '', ''])
    for filename in package.files or []:
        basename = Path(str(filename)).name.lower()
        if basename.startswith(('license', 'copying', 'notice')) and '.dist-info/' in str(filename):
            source = Path(package.locate_file(filename))
            if source.is_file():
                target = output / canonical / source.name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
    for specification in package.requires or []:
        requirement = Requirement(specification)
        if requirement.marker is None or requirement.marker.evaluate({'extra': ''}):
            pending.append(requirement.name)
notices.extend(['## Qt / PySide6',
    'Qt for Python: https://code.qt.io/cgit/pyside/pyside-setup.git/',
    'Qt source and third-party notices: https://code.qt.io/cgit/qt/',
    'https://doc.qt.io/qt-6/licenses-used-in-qt.html',
    'PySide6 metadata declares LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only.',
    'The application uses dynamically bundled Qt libraries. See the package notices above.',
    '', '## Python', 'https://docs.python.org/3/license.html', ''])
(output / 'NOTICES.md').write_text('\n'.join(notices))
