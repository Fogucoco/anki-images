# SPDX-License-Identifier: GPL-3.0-or-later
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import zipfile

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QApplication, QMessageBox
from app import Window
from i18n import resolve_language, set_language, tr
from deck_builder import build_files, georgian_speech


class LanguageAndWordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_locale_fallback(self):
        for locale in ('ru_RU', 'ru_GE'):
            self.assertEqual(resolve_language('system', locale), 'ru')
        for locale in ('en_US', 'en_GB', 'ka_GE', 'de_DE'):
            self.assertEqual(resolve_language('system', locale), 'en_US')
        self.assertEqual(resolve_language('ru', 'en_US'), 'ru')
        self.assertEqual(resolve_language('en_US', 'ru_RU'), 'en_US')
        set_language('ru')
        self.assertEqual(tr('Export Anki Deck…'), 'Экспортировать в Anki…')
        set_language('en_US')

    def test_text_only_export_georgian_audio(self):
        set_language('en_US')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            sound = root / 'sample.mp3'
            sound.write_bytes(b'test-audio')
            pairs = [
                {'id': 'one', 'front': 'წყალი', 'back': 'вода', 'direction': 'both'},
                {'id': 'two', 'front': 'cat', 'back': 'კატა (кот)', 'direction': 'forward'},
                {'id': 'three', 'front': 'English', 'back': 'Русский', 'direction': 'reverse'}]
            with patch('deck_builder.audio_for', return_value=sound) as audio:
                self.assertEqual(build_files([], root / 'words.apkg', 'Words', word_pairs=pairs), 3)
                self.assertEqual([call.args[0] for call in audio.call_args_list], ['წყალი', 'კატა'])
            with zipfile.ZipFile(root / 'words.apkg') as archive:
                self.assertEqual(len(json.loads(archive.read('media'))), 1)
                archive.extract('collection.anki2', root)
            with sqlite3.connect(root / 'collection.anki2') as db:
                self.assertEqual(db.execute('SELECT COUNT(*) FROM cards').fetchone()[0], 4)
                fields = [row[0].split('\x1f') for row in db.execute('SELECT flds FROM notes')]
                self.assertIn('[sound:', fields[0][0])
                self.assertNotIn('[sound:', fields[0][1])
                self.assertNotIn('[sound:', fields[1][0])
                self.assertIn('[sound:', fields[1][1])
                self.assertTrue(all('[sound:' not in field for field in fields[2]))
            self.assertEqual(georgian_speech('water вода'), '')

    def test_unified_list_selection_and_editing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            settings = QSettings(str(root / 'prefs.ini'), QSettings.Format.IniFormat)
            settings.setValue('language', 'en_US')
            folder = root / 'images'
            folder.mkdir()
            (folder / 'picture.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"/>')
            window = Window(settings)
            try:
                window.load_folder(folder)
                item = window.word_cards.insert_pair({'id': 'pair', 'front': 'წყალი', 'back': 'вода', 'direction': 'reverse'})
                window.word_cards.changed()
                window.images.setCurrentItem(item)
                window.word_edit.setText('კატა')
                window.word_changed('კატა')
                window.back_edit.setText('кот')
                window.pair_back_changed('кот')
                self.assertEqual(window.selected_speech(), 'კატა')
                self.assertEqual(window.images.topLevelItemCount(), 2)
                self.assertEqual(len(window.selected_files()), 1)
                window.set_all(False)
                self.assertEqual(window.word_cards.pairs(), [])
                self.assertEqual(window.selected_files(), [])
                window.set_all(True)
                window.load_folder(folder)
                self.assertEqual(window.images.topLevelItemCount(), 2)
                self.assertEqual(window.word_cards.pairs()[0]['front'], 'კატა')
                self.assertEqual(window.word_cards.pairs()[0]['back'], 'кот')
                self.assertEqual(window.word_cards.pairs()[0]['direction'], 'reverse')
                window.filter.setText('кот')
                self.assertEqual(sum(not window.images.topLevelItem(i).isHidden() for i in range(2)), 1)
                output = root / 'unified.apkg'
                build_files(window.selected_files(), output, 'Unified', audio=False, word_pairs=window.word_cards.pairs())
                with zipfile.ZipFile(output) as archive:
                    archive.extract('collection.anki2', root)
                with sqlite3.connect(root / 'collection.anki2') as db:
                    self.assertEqual(db.execute('SELECT COUNT(*) FROM notes').fetchone()[0], 2)
                    self.assertEqual(db.execute('SELECT COUNT(*) FROM cards').fetchone()[0], 3)
            finally:
                window.close()

    def test_image_caption_renames_file_and_remove_deletes_selected_card(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / 'images'
            folder.mkdir()
            original = folder / 'picture.svg'
            original.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"/>')
            window = Window(QSettings(str(root / 'prefs.ini'), QSettings.Format.IniFormat))
            try:
                window.load_folder(folder)
                item = window.images.topLevelItem(0)
                window.images.setCurrentItem(item)
                window.directions['picture.svg'] = 'reverse'
                window.word_edit.setText('кот')
                window.word_changed('кот')
                window.word_editing_finished()
                renamed = folder / 'кот.svg'
                self.assertFalse(original.exists())
                self.assertTrue(renamed.exists())
                self.assertEqual(window.selected_files(), [renamed])
                self.assertEqual(item.data(0, Qt.ItemDataRole.UserRole), str(renamed))
                self.assertEqual(window.directions, {'кот.svg': 'reverse'})
                with patch('app.QMessageBox.question', return_value=QMessageBox.StandardButton.Yes):
                    window.remove_selected()
                self.assertFalse(renamed.exists())
                self.assertEqual(window.images.topLevelItemCount(), 0)
                pair = window.word_cards.insert_pair({'id': 'pair', 'front': 'წყალი', 'back': 'вода', 'direction': 'both'})
                window.images.setCurrentItem(pair)
                window.remove_selected()
                self.assertEqual(window.word_cards.pairs(False), [])
            finally:
                window.close()

    def test_folder_pairs_are_separate_and_preferences_ignored(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first, second = root / 'first', root / 'second'
            first.mkdir()
            second.mkdir()
            settings = QSettings(str(root / 'prefs.ini'), QSettings.Format.IniFormat)
            greeting = {'id': 'saved', 'front': 'გამარჯობა', 'back': 'привет', 'direction': 'both'}
            settings.setValue('word_pairs', json.dumps([greeting], ensure_ascii=False))
            window = Window(settings)
            try:
                self.assertEqual(window.word_cards.pairs(False), [])
                window.load_folder(first)
                window.word_cards.insert_pair(greeting)
                window.word_cards.changed()
                self.assertIn('გამარჯობა', (first / 'word-cards.json').read_text())
                window.load_folder(second)
                self.assertEqual(window.word_cards.pairs(False), [])
                window.load_folder(first)
                self.assertEqual(window.word_cards.pairs(False)[0]['front'], 'გამარჯობა')
                self.assertIsNone(settings.value('greeting_cleanup_v1'))
            finally:
                window.close()

    def test_ui_persistence_and_language_change(self):
        with tempfile.TemporaryDirectory() as temp:
            QSettings.setDefaultFormat(QSettings.Format.IniFormat)
            QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, temp)
            window = Window(QSettings(str(Path(temp) / 'settings.ini'), QSettings.Format.IniFormat))
            window.word_cards.insert_pair({'id': 'test', 'front': 'წყალი', 'back': 'вода', 'direction': 'reverse'})
            window.word_cards.changed()
            self.assertTrue(window.export_button.isEnabled())
            replacement = window.change_language('ru')
            self.assertEqual(replacement.tabs.tabText(0), 'Карточки')
            self.assertEqual(replacement.tabs.count(), 3)
            self.assertEqual(replacement.tabs.tabText(1), 'Поиск картинок')
            self.assertEqual(replacement.tabs.tabText(2), 'Озвучка')
            self.assertEqual(replacement.images.topLevelItemCount(), 1)
            self.assertEqual(replacement.word_cards.pairs()[0]['back'], 'вода')
            self.assertEqual(replacement.word_cards.pairs()[0]['direction'], 'reverse')
            replacement.close()
            set_language('en_US')


if __name__ == '__main__':
    unittest.main()
