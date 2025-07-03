import json
from PyQt5.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTextEdit, QMessageBox, QDialogButtonBox,
                             QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
                             QTabWidget, QListWidget, QInputDialog, QListWidgetItem)

class RuleManagerDialog(QDialog):
    def __init__(self, rules, parent=None):
        super().__init__(parent)
        self.rules = json.loads(json.dumps(rules))
        self.setWindowTitle("Parsing Rule Manager")
        self.setMinimumSize(800, 600)
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Rule Name", "Type", "Value", "Pattern (Regex)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        button_layout = QHBoxLayout()
        add_btn = QPushButton("Add Rule")
        add_btn.clicked.connect(self.add_row)
        remove_btn = QPushButton("Remove Selected Rule")
        remove_btn.clicked.connect(self.remove_row)
        button_layout.addWidget(add_btn)
        button_layout.addWidget(remove_btn)
        layout.addLayout(button_layout)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept_changes)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        self.populate_table()

    def populate_table(self):
        self.table.setRowCount(len(self.rules))
        for row, rule in enumerate(self.rules):
            self.table.setItem(row, 0, QTableWidgetItem(rule.get("name", "")))
            combo = QComboBox()
            combo.addItems(["extraction", "language_detect"])
            combo.setCurrentText(rule.get("type", "extraction"))
            self.table.setCellWidget(row, 1, combo)
            self.table.setItem(row, 2, QTableWidgetItem(rule.get("value", "")))
            self.table.setItem(row, 3, QTableWidgetItem(rule.get("pattern", "")))

    def accept_changes(self):
        new_rules = []
        for row in range(self.table.rowCount()):
            rule = {
                "name": self.table.item(row, 0).text(),
                "type": self.table.cellWidget(row, 1).currentText(),
                "value": self.table.item(row, 2).text(),
                "pattern": self.table.item(row, 3).text()
            }
            new_rules.append(rule)
        self.rules = new_rules
        self.accept()

    def add_row(self):
        self.table.insertRow(self.table.rowCount())
        new_row_index = self.table.rowCount() - 1
        self.table.setItem(new_row_index, 0, QTableWidgetItem("New Rule"))
        combo = QComboBox()
        combo.addItems(["extraction", "language_detect"])
        self.table.setCellWidget(new_row_index, 1, combo)
        self.table.setItem(new_row_index, 2, QTableWidgetItem(""))
        self.table.setItem(new_row_index, 3, QTableWidgetItem(""))

    def remove_row(self):
        current_row = self.table.currentRow()
        if current_row > -1:
            self.table.removeRow(current_row)
            
    def get_updated_rules(self):
        return self.rules

# La clase TemplateManagerDialog (copiada de leads.py)
class TemplateManagerDialog(QDialog):
    def __init__(self, templates, parent=None):
        super().__init__(parent)
        self.templates = json.loads(json.dumps(templates))
        self.setWindowTitle("Template Manager")
        self.setMinimumSize(800, 600)

        for lang_code, templates_value in self.templates.items():
            if isinstance(templates_value, str):
                self.templates[lang_code] = [templates_value]

        self.layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("innerTabWidget")
        self.layout.addWidget(self.tab_widget)
        self.template_lists = {}
        self.template_editors = {}
        for lang_code, template_list in self.templates.items():
            lang_tab = QWidget()
            lang_layout = QHBoxLayout(lang_tab)
            self.template_lists[lang_code] = QListWidget()
            self.template_lists[lang_code].setMaximumWidth(250)
            self.template_lists[lang_code].itemClicked.connect(self.display_template)
            for i, template_text in enumerate(template_list):
                self.template_lists[lang_code].addItem(f"Template {i+1}")
            self.template_editors[lang_code] = QTextEdit()
            lang_layout.addWidget(self.template_lists[lang_code])
            lang_layout.addWidget(self.template_editors[lang_code])
            self.tab_widget.addTab(lang_tab, lang_code.upper())
        action_layout = QHBoxLayout()
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_template)
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.save_template)
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_template)
        action_layout.addWidget(add_btn)
        action_layout.addWidget(save_btn)
        action_layout.addWidget(delete_btn)
        add_lang_btn = QPushButton("Add Language")
        add_lang_btn.clicked.connect(self.add_language_tab)
        action_layout.addWidget(add_lang_btn)
        delete_lang_btn = QPushButton("Delete Language")
        delete_lang_btn.clicked.connect(self.delete_language)
        action_layout.addWidget(delete_lang_btn)
        self.layout.addLayout(action_layout)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept_changes)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def accept_changes(self):
        self.save_template()
        self.accept()

    def get_current_lang(self):
        return self.tab_widget.tabText(self.tab_widget.currentIndex()).lower()

    def display_template(self, item):
        lang = self.get_current_lang()
        index = self.template_lists[lang].row(item)
        if 0 <= index < len(self.templates[lang]):
            self.template_editors[lang].setText(self.templates[lang][index])

    def add_template(self):
        lang = self.get_current_lang()
        list_widget = self.template_lists[lang]
        new_item_text = f"New Template {list_widget.count() + 1}"
        new_item = QListWidgetItem(new_item_text)
        list_widget.addItem(new_item)
        list_widget.setCurrentItem(new_item)
        self.template_editors[lang].clear()
        self.template_editors[lang].setFocus()

    def save_template(self):
        lang = self.get_current_lang()
        list_widget = self.template_lists[lang]
        current_row = list_widget.currentRow()
        if current_row == -1: return
        new_text = self.template_editors[lang].toPlainText()
        if not new_text: return
        if current_row < len(self.templates[lang]):
            self.templates[lang][current_row] = new_text
        else:
            self.templates[lang].append(new_text)
        list_widget.currentItem().setText(f"Template {current_row + 1}")

    def delete_template(self):
        lang = self.get_current_lang()
        list_widget = self.template_lists[lang]
        current_row = list_widget.currentRow()
        if current_row > -1 and QMessageBox.question(self, 'Confirm', 'Are you sure?') == QMessageBox.Yes:
            del self.templates[lang][current_row]
            list_widget.takeItem(current_row)
            self.template_editors[lang].clear()

    def get_updated_templates(self):
        return self.templates

    def add_language_tab(self):
        lang_code, ok = QInputDialog.getText(self, 'Add Language', 'Enter a 2-letter language code (e.g., es for Spanish):')
        if ok and lang_code and len(lang_code.strip()) == 2:
            lang_code = lang_code.lower().strip()
            if lang_code not in self.templates:
                self.templates[lang_code] = []
                lang_tab = QWidget()
                lang_layout = QHBoxLayout(lang_tab)
                self.template_lists[lang_code] = QListWidget()
                self.template_lists[lang_code].setMaximumWidth(250)
                self.template_lists[lang_code].itemClicked.connect(self.display_template)
                self.template_editors[lang_code] = QTextEdit()
                lang_layout.addWidget(self.template_lists[lang_code])
                lang_layout.addWidget(self.template_editors[lang_code])
                new_tab_index = self.tab_widget.addTab(lang_tab, lang_code.upper())
                self.tab_widget.setCurrentIndex(new_tab_index)
            else:
                QMessageBox.information(self, "Language Exists", f"The language '{lang_code}' already exists.")

    def delete_language(self):
        if self.tab_widget.count() <= 1:
            QMessageBox.warning(self, "Cannot Delete", "You cannot delete the last remaining language.")
            return
        current_index = self.tab_widget.currentIndex()
        lang_code = self.tab_widget.tabText(current_index).lower()
        reply = QMessageBox.question(self, 'Confirm Deletion',
                                     f"Are you sure you want to permanently delete the '{lang_code.upper()}' language and all its templates?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if lang_code in self.templates: del self.templates[lang_code]
            if lang_code in self.template_lists: del self.template_lists[lang_code]
            if lang_code in self.template_editors: del self.template_editors[lang_code]
            self.tab_widget.removeTab(current_index)
