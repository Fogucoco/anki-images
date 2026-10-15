# SPDX-License-Identifier: GPL-3.0-or-later
"""Editable text-only cards, stored as UTF-8 JSON beside the images."""
import json
import uuid
from PySide6.QtCore import Qt, QObject
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem, QComboBox, QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QMessageBox, QHeaderView, QCheckBox
from i18n import tr

def is_word_pair(item):
    return item is not None and bool(item.data(0, Qt.ItemDataRole.UserRole + 1))

class WordCardsPanel(QObject):
    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.table = owner.images
        self.load_failed = False

    @staticmethod
    def read_pairs(folder):
        path = folder / 'word-cards.json'
        pairs = json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
        if not isinstance(pairs, list):
            raise ValueError(tr('Invalid word-pair data'))
        for pair in pairs:
            if not isinstance(pair, dict) or not all(isinstance(pair.get(k), str) for k in ('id', 'front', 'back')) or pair.get('direction', 'both') not in ('both', 'forward', 'reverse'):
                raise ValueError(tr('Invalid word-pair data'))
        return pairs

    def insert_pair(self, pair):
        blocked = self.table.blockSignals(True)
        item = QTreeWidgetItem()
        item.setData(0, Qt.ItemDataRole.UserRole, pair['id'])
        item.setData(0, Qt.ItemDataRole.UserRole + 1, True)
        item.setData(0, Qt.ItemDataRole.UserRole + 2, dict(pair))
        item.setText(0, self.label(pair))
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(0, Qt.CheckState.Checked if pair.get('enabled', True) else Qt.CheckState.Unchecked)
        self.table.addTopLevelItem(item)
        combo = QComboBox()
        for label, value in [('Both ↔', 'both'), ('Front → Back', 'forward'), ('Back → Front', 'reverse')]:
            combo.addItem(tr(label), value)
        combo.setCurrentIndex(combo.findData(pair.get('direction', 'both')))
        combo.currentIndexChanged.connect(self.changed)
        holder = QWidget()
        row = QVBoxLayout(holder)
        row.setContentsMargins(4, 2, 4, 2)
        row.addWidget(combo, 0, Qt.AlignmentFlag.AlignVCenter)
        self.table.setItemWidget(item, 1, holder)
        self.table.blockSignals(blocked)
        return item

    @staticmethod
    def label(pair):
        return tr('Text · {front} ↔ {back}').format(front=pair['front'], back=pair['back'])

    def pairs(self, selected_only=True):
        result = []
        for index in range(self.table.topLevelItemCount()):
            item = self.table.topLevelItem(index)
            if not is_word_pair(item):
                continue
            enabled = item.checkState(0) == Qt.CheckState.Checked
            if selected_only and not enabled:
                continue
            pair = dict(item.data(0, Qt.ItemDataRole.UserRole + 2))
            pair.update(direction=self.table.itemWidget(item, 1).findChild(QComboBox).currentData(), enabled=enabled)
            result.append(pair)
        return result

    def changed(self, *_):
        if self.owner.folder is not None:
            try:
                import tempfile
                from pathlib import Path
                with tempfile.TemporaryDirectory(dir=self.owner.folder) as temp:
                    path = Path(temp) / 'word-cards.json'
                    path.write_text(json.dumps(self.pairs(False), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
                    path.replace(self.owner.folder / 'word-cards.json')
            except OSError as error:
                QMessageBox.warning(self.owner, tr('Unable to Save Word Pairs'), str(error))
        if hasattr(self.owner, 'export_button'):
            self.owner.selection_changed()

    def add_pair(self):
        if self.load_failed:
            QMessageBox.warning(self.owner, tr('Unable to Save Word Pairs'), tr('Saved word pairs are unreadable. Resolve the saved data before adding new pairs.'))
            return
        dialog = QDialog(self.owner)
        dialog.setWindowTitle(tr('Add Word Pair'))
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        front, back = (QLineEdit(), QLineEdit())
        front.setPlaceholderText(tr('e.g. წყალი'))
        back.setPlaceholderText(tr('e.g. water'))
        form.addRow(tr('Front'), front)
        form.addRow(tr('Back'), back)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(tr('Add'))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(tr('Cancel'))
        buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

        def validate():
            buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(bool(front.text().strip() and back.text().strip()))
        front.textChanged.connect(validate)
        back.textChanged.connect(validate)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            item = self.insert_pair({'id': uuid.uuid4().hex, 'front': front.text().strip(), 'back': back.text().strip(), 'direction': 'both'})
            self.owner.filter.clear()
            self.table.setCurrentItem(item)
            self.owner.filter_images()
            self.changed()

    def remove_pair(self):
        item = self.table.currentItem()
        if is_word_pair(item):
            self.table.takeTopLevelItem(self.table.indexOfTopLevelItem(item))
            self.changed()
