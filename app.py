# SPDX-License-Identifier: GPL-3.0-or-later
"""Anki Images: desktop deck builder and independent Eka speech player."""
import asyncio
import json
import os
import tempfile
from pathlib import Path
import sys
from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QLocale, QObject, QRunnable, QSettings, QSize, Qt, QThreadPool, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QIcon, QPixmap
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import QAbstractItemView, QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPlainTextEdit, QProgressBar, QPushButton, QSplitter, QTabWidget, QTreeWidget, QTreeWidgetItem, QHeaderView, QVBoxLayout, QWidget
from deck_builder import VOICE, build_files, find_images, georgian_speech, cleanup_audio_cache
import edge_tts
from search_ui import ImageSearchPanel
from word_cards import WordCardsPanel, is_word_pair
from i18n import tr, set_language

class Signals(QObject):
    done = Signal(object)
    failed = Signal(str)
    progress = Signal(int, int, str)

class Task(QRunnable):

    def __init__(self, function):
        super().__init__()
        self.function = function
        self.signals = Signals()

    def run(self):
        try:
            self.signals.done.emit(self.function(self.signals.progress.emit))
        except Exception as error:
            self.signals.failed.emit(str(error))

async def speech_bytes(text):
    data = bytearray()
    async for chunk in edge_tts.Communicate(text, VOICE).stream():
        if chunk['type'] == 'audio':
            data.extend(chunk['data'])
    if not data:
        raise RuntimeError(tr('The speech service returned no audio.'))
    return bytes(data)

class Window(QMainWindow):

    def __init__(self, settings=None):
        super().__init__()
        self.setWindowTitle(tr('Anki Images'))
        self.resize(1080, 820)
        self.setMinimumSize(760, 580)
        self.settings = settings if settings is not None else QSettings('AnkiImages', 'Anki Images')
        set_language(str(self.settings.value('language', 'system')))
        self.pool = QThreadPool(self)
        self.tasks = {}
        self.folder = None
        self.words = {}
        self.directions = {}
        self.credits = {}
        self.export_multiplier = 2
        self.export_busy = False
        self.exported = None
        self.buffer = None
        self.cache = Path.home() / 'Library' / 'Caches' / 'Anki Images' / 'audio'
        self.audio_output = QAudioOutput(self)
        self.audio_output.setVolume(1.0)
        self.player = QMediaPlayer(self)
        self.player.setAudioOutput(self.audio_output)
        self.player.errorOccurred.connect(self.audio_error)
        self.player.mediaStatusChanged.connect(self.media_status)
        self.player.playbackStateChanged.connect(self.playback_state)
        content = QWidget()
        outer = QVBoxLayout(content)
        outer.setContentsMargins(24, 20, 24, 20)
        title = QLabel(tr('Anki Images'))
        title.setStyleSheet('font-size: 26px; font-weight: 700;')
        top = QHBoxLayout()
        top.addWidget(title, 1)
        top.addWidget(self.button(tr('Settings…'), self.open_settings))
        outer.addLayout(top)
        subtitle = QLabel(tr('Build picture decks. Practice Georgian pronunciation.'))
        subtitle.setStyleSheet('color: #77808d; margin-bottom: 12px;')
        outer.addWidget(subtitle)
        self.tabs = QTabWidget()
        self.tabs.addTab(self.cards_tab(), tr('Cards'))
        self.search_panel = ImageSearchPanel(self)
        self.tabs.addTab(self.search_panel, tr('Image Search'))
        self.tabs.addTab(self.voice_tab(), tr('Voice Studio'))
        self.word_cards = WordCardsPanel(self)
        self.images.itemChanged.connect(self.word_cards.changed)
        if self.images.topLevelItemCount():
            self.images.setCurrentItem(self.images.topLevelItem(0))
        self.selection_changed()
        outer.addWidget(self.tabs)
        self.setCentralWidget(content)
        self.statusBar().showMessage(tr('Ready'))
        self.selection_changed()

    def open_settings(self):
        if self.tasks:
            QMessageBox.information(self, tr('Operation in Progress'), tr('Wait for the current operation to finish before changing the language.'))
            return
        dialog = QDialog(self)
        dialog.setWindowTitle(tr('Settings'))
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        choice = QComboBox()
        choice.addItem(tr('System'), 'system')
        choice.addItem('English (US)', 'en_US')
        choice.addItem('Русский', 'ru')
        choice.setCurrentIndex(max(0, choice.findData(self.settings.value('language', 'system'))))
        form.addRow(tr('Interface language'), choice)
        layout.addLayout(form)
        layout.addWidget(QLabel(tr('Other system languages use English (US).')))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Apply).setText(tr('Apply'))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(tr('Cancel'))
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.change_language(choice.currentData())

    def change_language(self, preference):
        self.settings.setValue('language', preference)
        self.save_word_edits()
        selected = {p.name for p in self.selected_files()}
        replacement = Window(self.settings)
        if self.folder is not None:
            replacement.load_folder(self.folder)
            for index in range(replacement.images.topLevelItemCount()):
                item = replacement.images.topLevelItem(index)
                if is_word_pair(item):
                    continue
                filename = Path(item.data(0, Qt.ItemDataRole.UserRole)).name
                item.setCheckState(0, Qt.CheckState.Checked if filename in selected else Qt.CheckState.Unchecked)
        if self.folder is None:
            for pair in self.word_cards.pairs(False):
                replacement.word_cards.insert_pair(pair)
            replacement.selection_changed()
        replacement.deck_name.setText(self.deck_name.text())
        replacement.include_audio.setChecked(self.include_audio.isChecked())
        replacement.text.setPlainText(self.text.toPlainText())
        replacement.filter.setText(self.filter.text())
        replacement.search_panel.set_word(self.search_panel.word.text())
        replacement.tabs.setCurrentIndex(self.tabs.currentIndex())
        replacement.resize(self.size())
        QApplication.instance().main_window = replacement
        replacement.show()
        self.close()
        self.deleteLater()
        return replacement

    def button(self, text, callback):
        button = QPushButton(text)
        button.clicked.connect(callback)
        button.setMinimumHeight(32)
        return button

    def cards_tab(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        row = QHBoxLayout()
        self.choose = self.button(tr('Choose Folder…'), self.choose_folder)
        row.addWidget(self.choose)
        self.add_pair_button = self.button(tr('Add Word Pair…'), lambda: self.word_cards.add_pair())
        row.addWidget(self.add_pair_button)
        self.remove_button = self.button(tr('Remove'), self.remove_selected)
        self.remove_button.setEnabled(False)
        row.addWidget(self.remove_button)
        self.folder_label = QLabel(tr('No folder selected'))
        self.folder_label.setWordWrap(True)
        row.addWidget(self.folder_label, 1)
        layout.addLayout(row)
        toolbar = QHBoxLayout()
        self.select_all = self.button(tr('Select All'), lambda: self.set_all(True))
        self.deselect_all = self.button(tr('Deselect All'), lambda: self.set_all(False))
        toolbar.addWidget(self.select_all)
        toolbar.addWidget(self.deselect_all)
        self.filter = QLineEdit()
        self.filter.setPlaceholderText(tr('Filter by word or filename…'))
        self.filter.setClearButtonEnabled(True)
        self.filter.textChanged.connect(self.filter_images)
        toolbar.addWidget(self.filter, 1)
        self.count = QLabel(tr('0 selected · 0 cards'))
        toolbar.addWidget(self.count)
        layout.addLayout(toolbar)
        split = QSplitter()
        self.images = QTreeWidget()
        self.images.setColumnCount(2)
        self.images.setHeaderLabels([tr('Card'), tr('Card Direction')])
        self.images.setRootIsDecorated(False)
        self.images.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.images.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.images.header().setStretchLastSection(False)
        self.images.setColumnWidth(1, 160)
        self.images.setIconSize(QSize(56, 56))
        self.images.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.images.itemChanged.connect(self.selection_changed)
        self.images.currentItemChanged.connect(self.show_preview)
        self.images.setAccessibleName(tr('Images to include in the deck'))
        split.addWidget(self.images)
        preview_panel = QWidget()
        preview_layout = QVBoxLayout(preview_panel)
        self.preview = QLabel(tr('Choose a folder or add a word pair to get started.'))
        self.preview.setTextFormat(Qt.TextFormat.PlainText)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumSize(260, 230)
        self.preview.setWordWrap(True)
        preview_layout.addWidget(self.preview, 1)
        self.preview_title = QLabel('')
        self.preview_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_title.setWordWrap(True)
        preview_layout.addWidget(self.preview_title)
        self.front_label = QLabel(tr('Word on card'))
        preview_layout.addWidget(self.front_label)
        self.word_edit = QLineEdit()
        self.word_edit.setPlaceholderText(tr('Select an image to edit its word'))
        self.word_edit.setAccessibleName(tr('Word on selected card'))
        self.word_edit.setEnabled(False)
        self.word_edit.textEdited.connect(self.word_changed)
        self.word_edit.editingFinished.connect(self.word_editing_finished)
        preview_layout.addWidget(self.word_edit)
        self.back_label = QLabel(tr('Back'))
        self.back_edit = QLineEdit()
        self.back_edit.textEdited.connect(self.pair_back_changed)
        self.back_label.hide()
        self.back_edit.hide()
        preview_layout.addWidget(self.back_label)
        preview_layout.addWidget(self.back_edit)
        word_buttons = QHBoxLayout()
        self.listen_word = self.button(tr('Listen with Eka'), self.speak_selected)
        self.find_image = self.button(tr('Find Images…'), self.find_selected_image)
        self.listen_word.setEnabled(False)
        self.find_image.setEnabled(False)
        word_buttons.addWidget(self.listen_word)
        word_buttons.addWidget(self.find_image)
        preview_layout.addLayout(word_buttons)
        split.addWidget(preview_panel)
        split.setSizes([430, 450])
        layout.addWidget(split, 1)
        form = QFormLayout()
        self.deck_name = QLineEdit(str(self.settings.value('deck_name', 'Georgian Vocabulary')))
        self.deck_name.textChanged.connect(self.selection_changed)
        form.addRow(tr('Deck name'), self.deck_name)
        layout.addLayout(form)
        self.include_audio = QCheckBox(tr('Include Eka pronunciation'))
        self.include_audio.setChecked(True)
        layout.addWidget(self.include_audio)
        hint = QLabel(tr('Images and word pairs belong to this deck. Choose each card’s direction in its row.'))
        hint.setWordWrap(True)
        hint.setStyleSheet('color: #77808d; font-size: 12px;')
        layout.addWidget(hint)
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        footer = QHBoxLayout()
        self.export_status = QLabel(tr('Choose a folder or add a word pair to get started.'))
        self.export_status.setWordWrap(True)
        footer.addWidget(self.export_status, 1)
        self.reveal = self.button(tr('Show in Finder'), self.reveal_export)
        self.reveal.setVisible(False)
        footer.addWidget(self.reveal)
        self.export_button = self.button(tr('Export Anki Deck…'), self.export)
        self.export_button.setEnabled(False)
        self.export_button.setDefault(True)
        footer.addWidget(self.export_button)
        layout.addLayout(footer)
        self.select_all.setEnabled(False)
        self.deselect_all.setEnabled(False)
        return panel

    def voice_tab(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 22, 22, 22)
        heading = QLabel(tr('Listen with Eka'))
        heading.setStyleSheet('font-size: 21px; font-weight: 600;')
        layout.addWidget(heading)
        layout.addWidget(QLabel(tr('Georgian · Microsoft Eka')))
        self.text = QPlainTextEdit()
        self.text.setPlaceholderText(tr('Type or paste Georgian text here…'))
        self.text.setStyleSheet('font-size: 20px;')
        self.text.setAccessibleName(tr('Text to speak'))
        self.text.textChanged.connect(self.update_play)
        layout.addWidget(self.text, 1)
        self.voice_status = QLabel(tr('Audio plays here. No audio file is saved.\nInternet required; text is sent to Microsoft’s speech service.'))
        self.voice_status.setWordWrap(True)
        layout.addWidget(self.voice_status)
        controls = QHBoxLayout()
        controls.addStretch()
        self.stop_button = self.button(tr('Stop'), self.player.stop)
        self.stop_button.setEnabled(False)
        controls.addWidget(self.stop_button)
        self.play_button = self.button(tr('Play'), self.speak)
        self.play_button.setEnabled(False)
        controls.addWidget(self.play_button)
        layout.addLayout(controls)
        return panel

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, tr('Choose Image Folder'), str(self.settings.value('folder', str(Path.home() / 'Pictures'))))
        if folder:
            self.load_folder(Path(folder))

    def load_folder(self, folder):
        try:
            files = find_images(folder)
        except OSError as error:
            QMessageBox.warning(self, tr('Unable to Open Folder'), str(error))
            return False
        try:
            metadata = self.read_metadata(folder)
            saved_pairs = self.word_cards.read_pairs(folder)
        except (OSError, ValueError, TypeError) as error:
            QMessageBox.warning(self, tr('Unable to Read Word Edits'), str(error))
            return False
        session_pairs = self.word_cards.pairs(False) if self.folder is None else []
        if session_pairs:
            saved_pairs.extend(session_pairs)
        self.folder = folder
        self.words = metadata.get('words', {})
        self.directions = metadata.get('directions', {})
        self.credits = metadata.get('sources', {})
        self.settings.setValue('folder', str(folder))
        self.folder_label.setText(str(folder))
        self.images.blockSignals(True)
        self.images.clear()
        for path in files:
            label = self.words.get(path.name, path.stem)
            item = QTreeWidgetItem([path.name if label == path.stem else f'{path.name} — {label}'])
            item.setData(0, Qt.ItemDataRole.UserRole, str(path))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(0, Qt.CheckState.Checked)
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                item.setIcon(0, QIcon(pixmap.scaled(56, 56, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)))
            self.images.addTopLevelItem(item)
            self.attach_direction(item, path)
        for pair in saved_pairs:
            self.word_cards.insert_pair(pair)
        self.images.blockSignals(False)
        if session_pairs:
            self.word_cards.changed()
        self.select_all.setEnabled(self.images.topLevelItemCount() > 0)
        self.deselect_all.setEnabled(self.images.topLevelItemCount() > 0)
        self.reveal.setVisible(False)
        self.export_status.setText(tr('Choose which images to include, then export.') if files else tr('No supported images found in this folder.'))
        if self.images.topLevelItemCount():
            self.images.setCurrentItem(self.images.topLevelItem(0))
        else:
            self.preview.clear()
            self.preview.setText(tr('No images to preview'))
            self.preview_title.clear()
            self.word_edit.clear()
            self.word_edit.setEnabled(False)
            self.listen_word.setEnabled(False)
            self.find_image.setEnabled(False)
        self.filter_images()
        self.selection_changed()
        return True

    def attach_direction(self, item, path):
        combo = QComboBox()
        combo.addItem(tr('Both ↔'), 'both')
        combo.addItem(tr('Word → Image'), 'forward')
        combo.addItem(tr('Image → Word'), 'reverse')
        combo.setAccessibleName(tr('Card direction for {value0}').format(value0=path.name))
        combo.setCurrentIndex(combo.findData(self.directions.get(path.name, 'both')))
        combo.currentIndexChanged.connect(lambda _: self.row_direction_changed(path.name, combo.currentData()))
        holder = QWidget()
        row_layout = QVBoxLayout(holder)
        row_layout.setContentsMargins(4, 2, 4, 2)
        row_layout.addWidget(combo, 0, Qt.AlignmentFlag.AlignVCenter)
        self.images.setItemWidget(item, 1, holder)

    def row_direction_changed(self, filename, direction):
        self.directions[filename] = direction
        self.selection_changed()
        self.save_word_edits()

    def selected_files(self):
        return [Path(self.images.topLevelItem(i).data(0, Qt.ItemDataRole.UserRole)) for i in range(self.images.topLevelItemCount()) if not is_word_pair(self.images.topLevelItem(i)) and self.images.topLevelItem(i).checkState(0) == Qt.CheckState.Checked]

    def set_all(self, checked):
        self.images.blockSignals(True)
        for index in range(self.images.topLevelItemCount()):
            self.images.topLevelItem(index).setCheckState(0, Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        self.images.blockSignals(False)
        self.word_cards.changed()
        self.selection_changed()

    def selection_changed(self, *_):
        count = len(self.selected_files())
        cards = sum((2 if self.directions.get(p.name, 'both') == 'both' else 1 for p in self.selected_files()))
        self.count.setText(tr('{value0} of {value1} selected · {value2} cards').format(value0=count, value1=self.images.topLevelItemCount(), value2=cards))
        pairs = self.word_cards.pairs() if hasattr(self, 'word_cards') else []
        cards += sum((2 if pair['direction'] == 'both' else 1 for pair in pairs))
        valid = all((pair['front'] and pair['back'] for pair in pairs)) and all((self.words.get(p.name, p.stem).strip() for p in self.selected_files()))
        self.count.setText(tr('{value0} images + {value1} word pairs · {value2} cards').format(value0=count, value1=len(pairs), value2=cards))
        self.select_all.setEnabled(bool(self.images.topLevelItemCount()) and not self.export_busy)
        self.deselect_all.setEnabled(bool(self.images.topLevelItemCount()) and not self.export_busy)
        self.export_button.setEnabled(bool(count or pairs) and valid and bool(self.deck_name.text().strip()) and (not self.export_busy))

    def show_preview(self, item, *_):
        if item is None:
            self.preview.clear()
            self.preview_title.clear()
            self.word_edit.clear()
            self.word_edit.setEnabled(False)
            self.back_edit.hide()
            self.back_label.hide()
            self.remove_button.setEnabled(False)
            self.listen_word.setEnabled(False)
            self.find_image.setEnabled(False)
            return
        pair = is_word_pair(item)
        self.remove_button.setEnabled(not self.export_busy)
        self.back_label.setVisible(pair)
        self.back_edit.setVisible(pair)
        self.front_label.setText(tr('Front') if pair else tr('Word on card'))
        self.find_image.setVisible(not pair)
        if pair:
            data = item.data(0, Qt.ItemDataRole.UserRole + 2)
            self.preview.clear()
            self.preview.setText(data['front'] + '\n↔\n' + data['back'])
            self.preview_title.setText(data['front'] + ' ↔ ' + data['back'])
            self.word_edit.setText(data['front'])
            self.back_edit.setText(data['back'])
            self.word_edit.setEnabled(not self.export_busy)
            self.back_edit.setEnabled(not self.export_busy)
            self.listen_word.setEnabled(bool(georgian_speech(data['front'] + ' ' + data['back'])) and 'voice' not in self.tasks)
            return
        path = Path(item.data(0, Qt.ItemDataRole.UserRole))
        pixmap = QPixmap(str(path))
        self.preview.clear()
        if pixmap.isNull():
            self.preview.setText(tr('Preview unavailable for this image'))
        else:
            self.preview.setPixmap(pixmap.scaled(400, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        word = self.words.get(path.name, path.stem)
        self.preview_title.setText(word)
        self.word_edit.setText(word)
        self.word_edit.setEnabled('export' not in self.tasks)
        self.listen_word.setEnabled(bool(word.strip()) and 'voice' not in self.tasks)
        self.find_image.setEnabled(bool(word.strip()))

    @staticmethod
    def read_metadata(folder):
        path = folder / '.anki-images.json'
        if not path.exists():
            return {}
        data = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(data, dict) or data.get('version') != 1:
            raise ValueError(tr('Unsupported .anki-images.json format. The existing file was not changed.'))
        for key in ('words', 'sources'):
            if not isinstance(data.get(key, {}), dict):
                raise ValueError(tr('Invalid {value0} in .anki-images.json').format(value0=key))
        if not all((isinstance(k, str) and isinstance(v, str) for k, v in data.get('words', {}).items())):
            raise ValueError(tr('Invalid word edits in .anki-images.json'))
        if not all((isinstance(k, str) and isinstance(v, dict) and all((isinstance(value, str) for value in v.values())) for k, v in data.get('sources', {}).items())):
            raise ValueError(tr('Invalid image credits in .anki-images.json'))
        directions = data.get('directions', {})
        if not isinstance(directions, dict) or any((value not in ('both', 'forward', 'reverse') for value in directions.values())):
            raise ValueError(tr('Invalid directions in .anki-images.json'))
        return data

    def save_word_edits(self):
        if self.folder is None:
            return
        try:
            with tempfile.TemporaryDirectory(dir=self.folder) as temp:
                path = Path(temp) / 'metadata.json'
                path.write_text(json.dumps({'version': 1, 'words': self.words, 'sources': self.credits, 'directions': self.directions}, ensure_ascii=False, indent=2), encoding='utf-8')
                path.replace(self.folder / '.anki-images.json')
            return True
        except OSError as error:
            QMessageBox.warning(self, tr('Could Not Save Word Edits'), tr('Your edits still apply for this session, but could not be saved: {value0}').format(value0=error))
            return False

    def word_changed(self, text):
        item = self.images.currentItem()
        if item is None:
            return
        if is_word_pair(item):
            self.edit_pair(item, front=text)
            return
        path = Path(item.data(0, Qt.ItemDataRole.UserRole))
        self.words[path.name] = text
        self.preview_title.setText(text)
        item.setText(0, path.name if text == path.stem else tr('{value0} — {value1}').format(value0=path.name, value1=text))
        self.listen_word.setEnabled(bool(text.strip()) and 'voice' not in self.tasks)
        self.find_image.setEnabled(bool(text.strip()))
        self.selection_changed()
        self.filter_images()

    def word_editing_finished(self):
        item = self.images.currentItem()
        if item is None or is_word_pair(item):
            self.save_word_edits()
            return
        path = Path(item.data(0, Qt.ItemDataRole.UserRole))
        caption = self.word_edit.text().strip()
        if not caption:
            QMessageBox.warning(self, tr('Invalid Image Name'), tr('Image names cannot be empty.'))
            self.word_edit.setText(path.stem)
            self.show_preview(item)
            return
        if Path(caption).name != caption or caption in ('.', '..'):
            QMessageBox.warning(self, tr('Invalid Image Name'), tr('Image names cannot contain path separators.'))
            self.word_edit.setText(path.stem)
            self.show_preview(item)
            return
        target = path.with_name(caption + path.suffix)
        if target != path:
            if target.exists():
                QMessageBox.warning(self, tr('Could Not Rename Image'), tr('An image named {value0} already exists.').format(value0=target.name))
                self.word_edit.setText(path.stem)
                self.show_preview(item)
                return
            try:
                path.rename(target)
            except OSError as error:
                QMessageBox.warning(self, tr('Could Not Rename Image'), str(error))
                self.word_edit.setText(path.stem)
                self.show_preview(item)
                return
            self.words.pop(path.name, None)
            for metadata in (self.directions, self.credits):
                if path.name in metadata:
                    metadata[target.name] = metadata.pop(path.name)
            item.setData(0, Qt.ItemDataRole.UserRole, str(target))
            item.setText(0, target.name)
        self.words.pop(target.name, None)
        self.save_word_edits()
        self.show_preview(item)

    def remove_selected(self):
        item = self.images.currentItem()
        if item is None or self.export_busy:
            return
        if is_word_pair(item):
            self.word_cards.remove_pair()
            return
        path = Path(item.data(0, Qt.ItemDataRole.UserRole))
        if QMessageBox.question(self, tr('Remove Image?'), tr('Remove {value0} from this folder? This cannot be undone.').format(value0=path.name)) != QMessageBox.StandardButton.Yes:
            return
        try:
            path.unlink()
        except OSError as error:
            QMessageBox.warning(self, tr('Could Not Remove Image'), str(error))
            return
        self.words.pop(path.name, None)
        self.directions.pop(path.name, None)
        self.credits.pop(path.name, None)
        self.images.takeTopLevelItem(self.images.indexOfTopLevelItem(item))
        self.save_word_edits()
        self.selection_changed()

    def pair_back_changed(self, text):
        item = self.images.currentItem()
        if is_word_pair(item):
            self.edit_pair(item, back=text)

    def edit_pair(self, item, **changes):
        data = dict(item.data(0, Qt.ItemDataRole.UserRole + 2))
        data.update(changes)
        self.images.blockSignals(True)
        item.setData(0, Qt.ItemDataRole.UserRole + 2, data)
        item.setText(0, self.word_cards.label(data))
        self.images.blockSignals(False)
        self.preview_title.setText(data['front'] + ' ↔ ' + data['back'])
        self.word_cards.changed()
        self.filter_images()
        self.update_play()

    def filter_images(self, *_):
        query = self.filter.text().strip().casefold()
        for index in range(self.images.topLevelItemCount()):
            item = self.images.topLevelItem(index)
            item.setHidden(query not in item.text(0).casefold())

    def find_selected_image(self):
        self.search_panel.set_word(self.word_edit.text().strip())
        self.tabs.setCurrentWidget(self.search_panel)

    def add_downloaded_image(self, target, word, credit):
        if self.folder == target.parent:
            existing_words = dict(self.words)
            existing_directions = dict(self.directions)
            existing_credits = dict(self.credits)
            checked = {p.name for p in self.selected_files()}
            if not self.load_folder(target.parent):
                raise OSError(tr('The image was saved, but the folder could not be loaded.'))
            self.words.update(existing_words)
            self.directions.update(existing_directions)
            self.credits.update(existing_credits)
        else:
            if not self.load_folder(target.parent):
                raise OSError(tr('The image was saved, but the folder could not be loaded.'))
            checked = {p.name for p in self.selected_files()}
        self.words[target.name] = word
        self.credits[target.name] = credit
        if not self.save_word_edits():
            raise OSError(tr('The image was saved, but its credits could not be saved.'))
        self.images.blockSignals(True)
        for index in range(self.images.topLevelItemCount()):
            item = self.images.topLevelItem(index)
            if is_word_pair(item):
                continue
            path = Path(item.data(0, Qt.ItemDataRole.UserRole))
            combo = self.images.itemWidget(item, 1).findChild(QComboBox)
            combo.blockSignals(True)
            combo.setCurrentIndex(combo.findData(self.directions.get(path.name, 'both')))
            combo.blockSignals(False)
            label = self.words.get(path.name, path.stem)
            item.setText(0, path.name if label == path.stem else tr('{value0} — {value1}').format(value0=path.name, value1=label))
            item.setCheckState(0, Qt.CheckState.Checked if path.name in checked or path == target else Qt.CheckState.Unchecked)
            if path == target:
                self.images.setCurrentItem(item)
        self.images.blockSignals(False)
        self.show_preview(self.images.currentItem())
        self.filter_images()
        self.selection_changed()

    def launch(self, key, function, success, failure):
        task = Task(function)
        self.tasks[key] = task

        def finish(value, failed=False):
            self.tasks.pop(key, None)
            (failure if failed else success)(value)
        task.signals.done.connect(lambda value: finish(value))
        task.signals.failed.connect(lambda error: finish(error, True))
        task.signals.progress.connect(self.export_progress)
        self.pool.start(task)

    def export(self):
        files = self.selected_files()
        name = self.deck_name.text().strip()
        pairs = self.word_cards.pairs()
        if not files and (not pairs) or not name:
            return
        if any((not pair['front'] or not pair['back'] for pair in pairs)):
            QMessageBox.warning(self, tr('Incomplete Word Pair'), tr('Enter text on both sides of each selected pair.'))
            return
        filename, _ = QFileDialog.getSaveFileName(self, tr('Export Anki Deck'), str(Path.home() / 'Documents' / 'Georgian Vocabulary.apkg'), 'Anki Deck (*.apkg)')
        if not filename:
            return
        output = Path(filename)
        if output.suffix.lower() != '.apkg':
            output = output.with_suffix('.apkg')
            if output.exists() and QMessageBox.question(self, tr('Replace Existing Deck?'), tr('Replace {value0}?').format(value0=output.name)) != QMessageBox.StandardButton.Yes:
                return
        self.settings.setValue('deck_name', name)
        audio = self.include_audio.isChecked()
        words = dict(self.words)
        credits = dict(self.credits)
        directions = dict(self.directions)
        self.export_card_count = sum((2 if directions.get(p.name, 'both') == 'both' else 1 for p in files)) + sum((2 if pair['direction'] == 'both' else 1 for pair in pairs))
        self.set_export_busy(True)
        self.export_status.setText(tr('Preparing deck…'))
        self.launch('export', lambda progress: (build_files(files, output, name, audio, self.cache, progress, words, 'both', credits, directions, pairs), output), self.export_done, self.export_failed)

    def set_export_busy(self, busy):
        self.export_busy = busy
        for widget in (self.choose, self.select_all, self.deselect_all, self.images, self.deck_name, self.include_audio, self.word_edit, self.filter, self.back_edit, self.add_pair_button, self.remove_button):
            widget.setEnabled(not busy)
        self.remove_button.setEnabled(not busy and self.images.currentItem() is not None)
        self.export_button.setEnabled(not busy and bool(self.selected_files()))
        self.selection_changed()
        self.progress.setVisible(busy)
        self.reveal.setVisible(False)
        self.progress.setValue(0)

    def export_progress(self, current, total, word):
        self.progress.setRange(0, total)
        self.progress.setValue(current)
        self.export_status.setText(tr('Processing {value0} of {value1}: {value2}').format(value0=current + 1, value1=total, value2=word) if current < total else tr('Finishing deck…'))

    def export_done(self, result):
        count, self.exported = result
        self.set_export_busy(False)
        self.reveal.setVisible(True)
        self.export_status.setText(tr('Exported {value0} cards from {value1} entries. Import the .apkg file into Anki.').format(value0=self.export_card_count, value1=count))
        self.statusBar().showMessage(str(self.exported))

    def export_failed(self, error):
        self.set_export_busy(False)
        self.export_status.setText(tr('Export failed. Your existing deck was not replaced.'))
        QMessageBox.warning(self, tr('Export Failed'), error)

    def reveal_export(self):
        if self.exported:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.exported.parent)))

    def update_play(self):
        if hasattr(self, 'play_button'):
            self.play_button.setEnabled(bool(self.text.toPlainText().strip()) and 'voice' not in self.tasks)
            self.listen_word.setEnabled(bool(self.selected_speech()) and 'voice' not in self.tasks)

    def speak(self):
        self.speak_text(self.text.toPlainText().strip())

    def selected_speech(self):
        if is_word_pair(self.images.currentItem()):
            return georgian_speech(self.word_edit.text() + ' ' + self.back_edit.text())
        return self.word_edit.text().strip()

    def speak_selected(self):
        self.speak_text(self.selected_speech())

    def speak_text(self, text):
        if 'voice' in self.tasks:
            return
        if not text:
            return
        if len(text) > 5000:
            QMessageBox.warning(self, tr('Text Too Long'), tr('Use 5,000 characters or fewer per playback.'))
            return
        self.player.stop()
        self.play_button.setEnabled(False)
        self.listen_word.setEnabled(False)
        self.statusBar().showMessage(tr('Generating Eka pronunciation…'))
        self.voice_status.setText(tr('Generating speech…'))
        self.launch('voice', lambda _: asyncio.run(asyncio.wait_for(speech_bytes(text), 60)), self.play_audio, self.voice_failed)

    def play_audio(self, data):
        self.player.setSource(QUrl())
        if self.buffer:
            self.buffer.close()
            self.buffer.deleteLater()
        self.buffer = QBuffer(self)
        self.buffer.setData(QByteArray(data))
        self.buffer.open(QIODevice.OpenModeFlag.ReadOnly)
        self.player.setSourceDevice(self.buffer, QUrl('audio.mp3'))
        self.player.play()
        self.voice_status.setText(tr('Playing with Eka. No audio file is saved.'))
        self.statusBar().showMessage(tr('Playing Eka pronunciation'))
        self.update_play()

    def voice_failed(self, error):
        self.update_play()
        self.voice_status.setText(tr('Could not generate speech. Check your internet connection and try again.'))
        self.statusBar().showMessage(tr('Speech unavailable'))
        QMessageBox.warning(self, tr('Speech Unavailable'), error or 'The request timed out.')

    def playback_state(self, state):
        self.stop_button.setEnabled(state == QMediaPlayer.PlaybackState.PlayingState)

    def media_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.voice_status.setText(tr('Ready. Audio was played without saving a file.'))
            self.statusBar().showMessage(tr('Ready'))

    def audio_error(self, *_):
        self.voice_status.setText(tr('Playback failed: {value0}').format(value0=self.player.errorString()))

    def closeEvent(self, event):
        if self.tasks:
            self.statusBar().showMessage(tr('Please wait for the current operation to finish before closing.'))
            event.ignore()
        else:
            self.player.stop()
            event.accept()

def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(Path(__file__).resolve().parent / 'assets' / 'app-icon.png')))
    app.setApplicationName('Anki Images')
    app.setOrganizationName('AnkiImages')
    window = Window()
    app.main_window = window
    window.show()
    window.launch('cache_cleanup', lambda progress: cleanup_audio_cache(window.cache),
                  lambda result: None, lambda error: window.statusBar().showMessage(error))
    return app.exec()
if __name__ == '__main__':
    sys.exit(main())
