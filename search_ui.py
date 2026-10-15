# SPDX-License-Identifier: GPL-3.0-or-later
from i18n import tr
'Image search panel with explicit image selection.'
from pathlib import Path
import re
from urllib.parse import urlencode
from PySide6.QtCore import QByteArray, QBuffer, QIODevice, QSize, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QIcon, QImage, QPixmap
from PySide6.QtWidgets import QAbstractItemView, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPushButton, QSplitter, QVBoxLayout, QWidget
from search_service import image_bytes, search_images

class ImageSearchPanel(QWidget):

    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.result_word = ''
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        row = QHBoxLayout()
        heading = QLabel(tr('Find a picture for your word'))
        heading.setStyleSheet('font-size: 20px; font-weight: 600;')
        row.addWidget(heading, 1)
        layout.addLayout(row)
        form = QFormLayout()
        self.word = QLineEdit()
        self.word.setPlaceholderText(tr('Search in any language, e.g. animal or ცხოველი'))
        self.word.setAccessibleName(tr('Image search query'))
        form.addRow(tr('Search query'), self.word)
        layout.addLayout(form)
        buttons = QHBoxLayout()
        self.search = owner.button(tr('Search Images'), self.start_search)
        buttons.addWidget(self.search)
        self.web = owner.button(tr('Open Google Images'), self.open_google)
        buttons.addWidget(self.web)
        buttons.addStretch()
        layout.addLayout(buttons)
        self.status = QLabel(tr('Search Wikimedia Commons. Your query is used exactly as entered; no translation or API key needed.'))
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        split = QSplitter()
        self.results = QListWidget()
        self.results.setViewMode(QListWidget.ViewMode.IconMode)
        self.results.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.results.setMovement(QListWidget.Movement.Static)
        self.results.setIconSize(QSize(145, 110))
        self.results.setGridSize(QSize(170, 160))
        self.results.setWordWrap(True)
        self.results.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.results.setAccessibleName(tr('Wikimedia image search results'))
        self.results.currentItemChanged.connect(self.show_result)
        split.addWidget(self.results)
        detail = QWidget()
        column = QVBoxLayout(detail)
        self.preview = QLabel(tr('Select a result to preview it'))
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumSize(220, 190)
        self.preview.setWordWrap(True)
        column.addWidget(self.preview, 1)
        self.credit = QLabel('')
        self.credit.setTextFormat(Qt.TextFormat.PlainText)
        self.credit.setWordWrap(True)
        self.credit.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        column.addWidget(self.credit)
        self.source = owner.button(tr('Open Source Page'), self.open_source)
        self.source.setEnabled(False)
        column.addWidget(self.source)
        self.add = owner.button(tr('Add Image to Folder…'), self.add_image)
        self.add.setEnabled(False)
        column.addWidget(self.add)
        split.addWidget(detail)
        split.setSizes([600, 300])
        layout.addWidget(split, 1)
        note = QLabel(tr('Only the image you choose is downloaded into your folder. Source and license credits are saved with it. Google Images opens your browser.'))
        note.setWordWrap(True)
        note.setStyleSheet('font-size: 12px; color: #77808d;')
        layout.addWidget(note)
        self.word.textEdited.connect(self.word_edited)
        self.word.returnPressed.connect(self.start_search)

    def set_word(self, word):
        self.word.setText(word)
        self.clear_results()

    def word_edited(self, *_):
        self.clear_results()

    def clear_results(self, *_):
        self.results.clear()
        self.add.setEnabled(False)
        self.source.setEnabled(False)
        self.preview.clear()
        self.preview.setText(tr('Select a result to preview it'))
        self.credit.clear()
        self.result_word = ''

    def busy(self, value):
        for widget in (self.word, self.search, self.results):
            widget.setEnabled(not value)
        self.add.setEnabled(not value and self.results.currentItem() is not None)
        self.source.setEnabled(not value and self.results.currentItem() is not None)

    def start_search(self):
        if 'image-search' in self.owner.tasks:
            return
        word = self.word.text().strip()
        if not word:
            self.status.setText(tr('Enter a search query first.'))
            return
        if len(word) > 200:
            self.status.setText(tr('Use 200 characters or fewer per search query.'))
            return
        self.clear_results()
        self.busy(True)
        self.status.setText(tr('Searching Wikimedia Commons…'))
        self.owner.launch('image-search', lambda _: (word, search_images(word)), self.search_done, self.failed)

    def search_done(self, data):
        word, (results, warnings) = data
        self.result_word = word
        self.results.blockSignals(True)
        for result in results:
            item = QListWidgetItem(result.title)
            item.setData(Qt.ItemDataRole.UserRole, result)
            item.setToolTip(f'{result.title}\nSearch: {result.query}\n{result.license}')
            if result.thumbnail:
                pixmap = QPixmap()
                if pixmap.loadFromData(result.thumbnail):
                    item.setIcon(QIcon(pixmap.scaled(145, 110, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)))
            self.results.addItem(item)
        self.results.blockSignals(False)
        summary = tr('{count} images · Query: {query}').format(count=len(results), query=word)
        if warnings:
            summary += '\n' + '\n'.join(warnings)
        if not results:
            summary += tr('\nTry a simpler query or open Google Images.')
        self.status.setText(summary)
        self.busy(False)
        if results:
            self.results.setCurrentRow(0)

    def failed(self, error):
        self.busy(False)
        self.status.setText(error)

    def show_result(self, item, *_):
        self.add.setEnabled(item is not None)
        self.source.setEnabled(item is not None)
        if item is None:
            return
        result = item.data(Qt.ItemDataRole.UserRole)
        self.preview.clear()
        pixmap = QPixmap()
        if result.thumbnail and pixmap.loadFromData(result.thumbnail):
            self.preview.setPixmap(pixmap.scaled(300, 240, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            self.preview.setText(tr('Preview unavailable; you can open the source page.'))
        self.credit.setText(tr('{value0}\n\n{value1}\n{value2}\nSearch: {value3}').format(value0=result.title, value1=result.artist[:240], value2=result.license, value3=result.query))

    def open_source(self):
        if self.results.currentItem():
            result = self.results.currentItem().data(Qt.ItemDataRole.UserRole)
            QDesktopServices.openUrl(QUrl(result.source_url))

    def open_google(self):
        query = self.word.text().strip()
        if not query:
            self.status.setText(tr('Enter the search query first.'))
            return
        QDesktopServices.openUrl(QUrl('https://www.google.com/search?' + urlencode({'tbm': 'isch', 'q': query, 'safe': 'active'})))

    def add_image(self):
        item = self.results.currentItem()
        if item is None or 'image-download' in self.owner.tasks:
            return
        if self.owner.export_busy:
            self.status.setText(tr('Wait for the deck export to finish before adding an image.'))
            return
        word = self.result_word.strip()
        if not word or word in {'.', '..'} or re.search('[/\\\\\\x00-\\x1f]', word):
            QMessageBox.warning(self, tr('Invalid Word'), tr('The word cannot contain slashes or control characters.'))
            return
        if len(word.encode('utf-8')) > 200:
            QMessageBox.warning(self, tr('Word Too Long'), tr('Use a shorter query for the image filename.'))
            return
        folder = self.owner.folder
        if folder is None:
            chosen = QFileDialog.getExistingDirectory(self, tr('Choose Folder for Downloaded Image'), str(Path.home() / 'Pictures'))
            if not chosen:
                return
            folder = Path(chosen)
        result = item.data(Qt.ItemDataRole.UserRole)
        self.busy(True)
        self.status.setText(tr('Downloading selected image…'))
        self.owner.launch('image-download', lambda _: (image_bytes(result.image_url), folder, word, result), self.download_done, self.failed)

    def download_done(self, data):
        raw, folder, word, result = data
        image = QImage.fromData(raw)
        if image.isNull() or image.width() * image.height() > 40000000:
            self.failed('This image could not be decoded, or is too large. Choose another result.')
            return
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        if not image.save(buffer, 'PNG'):
            self.failed('Could not prepare this image.')
            return
        target = folder / f'{word}.png'
        suffix = 2
        while target.exists():
            target = folder / f'{word}-{suffix}.png'
            suffix += 1
        try:
            with target.open('xb') as handle:
                handle.write(bytes(buffer.data()))
            self.owner.add_downloaded_image(target, word, result.credit())
        except Exception as error:
            self.failed(f'Could not add the image: {error}')
            return
        self.busy(False)
        self.status.setText(tr('Added {value0}. It is selected in Flashcards. Source and license credits saved.').format(value0=target.name))
