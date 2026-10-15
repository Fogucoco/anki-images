# SPDX-License-Identifier: GPL-3.0-or-later
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
import zipfile

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication, QComboBox
from PySide6.QtCore import QSettings, Qt
from app import Window
from deck_builder import build_files


class DirectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_mixed_directions_and_persistence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            QSettings.setDefaultFormat(QSettings.Format.IniFormat)
            QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(root / 'settings'))
            for name in ('a', 'b', 'c'):
                (root / f'{name}.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"/>')
            settings = QSettings(str(root / 'settings.ini'), QSettings.Format.IniFormat)
            settings.setValue('language', 'en_US')
            window = Window(settings)
            try:
                self.assertTrue(window.load_folder(root))
                self.assertEqual(len(window.selected_files()), 3)
                for row, mode in enumerate(('forward', 'reverse', 'both')):
                    item = window.images.topLevelItem(row)
                    combo = window.images.itemWidget(item, 1).findChild(QComboBox)
                    combo.setCurrentIndex(combo.findData(mode))
                self.assertIn('4 cards', window.count.text())
                window.filter.setText('b.svg')
                self.assertEqual(len(window.selected_files()), 3)
                self.assertFalse(window.images.topLevelItem(1).isHidden())
                window.load_folder(root)
                self.assertEqual({name: window.directions.get(name, 'both') for name in ('a.svg', 'b.svg', 'c.svg')}, {'a.svg': 'forward', 'b.svg': 'reverse', 'c.svg': 'both'})
                output = root / 'test.apkg'
                build_files(window.selected_files(), output, 'Mixed', audio=False, directions=window.directions)
                with zipfile.ZipFile(output) as archive:
                    archive.extract('collection.anki2', root)
                with sqlite3.connect(root / 'collection.anki2') as database:
                    self.assertEqual(database.execute('SELECT COUNT(*) FROM cards').fetchone()[0], 4)
                    rows = database.execute('SELECT n.flds, COUNT(*) FROM notes n JOIN cards c ON c.nid=n.id GROUP BY n.id').fetchall()
                    self.assertEqual({fields.split('\x1f')[0]: count for fields, count in rows}, {'a': 1, 'b': 1, 'c': 2})
                    models = json.loads(database.execute('SELECT models FROM col').fetchone()[0])
                    self.assertEqual(models['1834109278']['tmpls'][0]['qfmt'], '{{Image}}')
                    self.assertEqual(models['1834109277']['tmpls'][0]['qfmt'], '{{Title}}')
                self.assertFalse(hasattr(window.search_panel, 'api_key'))
                self.assertFalse(hasattr(window.search_panel, 'english'))
            finally:
                window.close()


if __name__ == '__main__':
    unittest.main()
