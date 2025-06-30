import json
import os
import random
import re
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QTextEdit, QMessageBox, QDialog, QDialogButtonBox,
                             QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
                             QFormLayout, QLineEdit, QTabWidget, QListWidget)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
import pyperclip

class PasteDetectTextEdit(QTextEdit):
    pasted = pyqtSignal()
    def insertFromMimeData(self, source):
        super().insertFromMimeData(source)
        self.pasted.emit()

class CorrectionDialog(QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Correct Parsed Information")
        self.setMinimumWidth(400)
        self.data = data
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_input = QLineEdit(data.get("name", ""))
        self.machine_input = QLineEdit(data.get("machine", ""))
        self.location_input = QLineEdit(data.get("location", ""))
        self.link_input = QLineEdit(data.get("link", ""))
        
        form_layout.addRow("Client Name:", self.name_input)
        form_layout.addRow("Machine Name:", self.machine_input)
        form_layout.addRow("Location:", self.location_input)
        form_layout.addRow("Link:", self.link_input)
        
        layout.addLayout(form_layout)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def get_corrected_data(self):
        return {
            "name": self.name_input.text(),
            "machine": self.machine_input.text(),
            "location": self.location_input.text(),
            "link": self.link_input.text()
        }

class LeadsTab(QWidget):
    output_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.used_templates = []
        self.templates_file = "templates/templates.json"
        self.rules_file = "regex/parsing_rules.json"
        self.load_templates()
        self.load_rules()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        self.warning_label = QLabel("Warning: Please double check the generated template!")
        self.warning_label.setStyleSheet("font-weight: bold; color: orange;")
        main_layout.addWidget(self.warning_label)
        title_label = QLabel("Paste the client message below and click 'Generate Template'")
        main_layout.addWidget(title_label)
        self.textbox = PasteDetectTextEdit()
        self.textbox.pasted.connect(self.on_paste)
        self.textbox.setPlaceholderText("Paste client message here...")
        main_layout.addWidget(self.textbox)
        button_layout = QHBoxLayout()
        generate_button = QPushButton("Generate Template")
        generate_button.clicked.connect(self.process_text)
        manage_templates_button = QPushButton("Manage Templates")
        manage_templates_button.clicked.connect(self.open_template_manager)
        manage_rules_button = QPushButton("Manage Parsing Rules")
        manage_rules_button.clicked.connect(self.open_rule_manager)
        button_layout.addWidget(generate_button)
        button_layout.addWidget(manage_templates_button)
        button_layout.addWidget(manage_rules_button)
        main_layout.addLayout(button_layout)
        self.status_label = QLabel("")
        main_layout.addWidget(self.status_label)

    def on_paste(self):
        QTimer.singleShot(50, self.process_text)

    def update_status(self, message, color="black"):
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color};")
        self.output_message.emit(f"[Leads Tab] {message.splitlines()[0]}...")

    def detect_language(self, text):
        text_lower = text.lower()
        for rule in self.rules:
            if rule.get('type') == 'language_detect':
                if re.search(rule.get('pattern', ''), text_lower, re.IGNORECASE):
                    return rule.get('value')
        return "en"

    # --- MODIFIED: Parsing is now done on raw text without pre-formatting ---
    def parse_input(self, text):
        results = {"name": "", "machine": "", "location": "", "link": ""}
        
        # Apply rules directly to the raw text
        for rule in self.rules:
            if rule.get('type') == 'extraction':
                field = rule.get('value')
                pattern = rule.get('pattern')
                
                # Only try to fill empty fields
                if field and pattern and not results.get(field):
                    try:
                        # Use multiline flag for patterns that use ^ or $
                        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                        if match and match.groups():
                            # Clean up the captured group only
                            results[field] = match.group(1).strip().rstrip('.')
                    except re.error as e:
                        print(f"Regex error in rule '{rule.get('name')}': {e}")
                        
        # Find links separately as this is very reliable
        links = re.findall(r"https?://\S+", text)
        if not results['link'] and links:
            results['link'] = links[0]
            
        return results

    def process_text(self):
        text = self.textbox.toPlainText().strip()
        if not text:
            self.update_status("Please paste some text first.", color="orange")
            return
        lang = self.detect_language(text)
        parsed_data = self.parse_input(text)
        if not all(parsed_data.values()):
            dialog = CorrectionDialog(parsed_data, self)
            if dialog.exec_() == QDialog.Accepted:
                final_data = dialog.get_corrected_data()
                if not all(final_data.values()):
                    QMessageBox.warning(self, "Incomplete Information", "All fields must be filled out.")
                    return
                self.generate_and_copy(final_data, lang)
            else:
                self.update_status("Template generation cancelled.", color="orange")
        else:
            self.generate_and_copy(parsed_data, lang)

    def generate_and_copy(self, data, lang):
        template = self.select_template(lang)
        final_message = template.format(
            client_name=data["name"],
            machine_name=data["machine"],
            location=data["location"],
            link=data["link"]
        )
        pyperclip.copy(final_message)
        self.textbox.clear()
        self.update_status("Template generated and copied to clipboard!", color="green")

    def select_template(self, language):
        if language in self.templates and self.templates[language]:
            return random.choice(self.templates[language])
        return "Template not found."

    def load_rules(self):
        try:
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                self.rules = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.rules = [
                {"name": "Detect Language: French", "type": "language_detect", "value": "fr", "pattern": "bonjour|votre intérêt|localisation"},
                {"name": "Detect Language: Italian", "type": "language_detect", "value": "it", "pattern": "buongiorno|gentile|località|interesse per"},
                {"name": "Extract: Client Name", "type": "extraction", "value": "name", "pattern": "(?:Dear|Hello|Bonjour|Cher|Gentile|Ciao)\\s+([\\w\\s.'-]+?)\\s*,"},
                {"name": "Extract: Machine Name", "type": "extraction", "value": "machine", "pattern": "(?:interest in our machine|machine|votre intérêt pour notre machine|interesse per (?:la|la nostra) macchina)\\s*:\\s*([^\\r\\n]*)"},
                {"name": "Extract: Location", "type": "extraction", "value": "location", "pattern": "(?:Location|Localisation|Località)\\s*:\\s*([^\\r\\n]*)"}
            ]
            self.save_rules()

    def save_rules(self):
        with open(self.rules_file, 'w', encoding='utf-8') as f:
            json.dump(self.rules, f, indent=2, ensure_ascii=False)

    def open_rule_manager(self):
        dialog = RuleManagerDialog(self.rules, self)
        if dialog.exec_() == QDialog.Accepted:
            self.rules = dialog.get_updated_rules()
            self.save_rules()
            self.update_status("Parsing rules updated successfully.", "green")
            
    def load_templates(self):
        try:
            with open(self.templates_file, 'r', encoding='utf-8') as f:
                self.templates = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.templates = {"en": ["Hello {client_name}, ..."], "it": [], "fr": []}
            self.save_templates()

    def save_templates(self):
        with open(self.templates_file, 'w', encoding='utf-8') as f:
            json.dump(self.templates, f, indent=2, ensure_ascii=False)

    def open_template_manager(self):
        dialog = TemplateManagerDialog(self.templates, self)
        if dialog.exec_() == QDialog.Accepted:
            self.templates = dialog.get_updated_templates()
            self.save_templates()

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

class TemplateManagerDialog(QDialog):
    def __init__(self, templates, parent=None):
        super().__init__(parent)
        self.templates = json.loads(json.dumps(templates))
        self.setWindowTitle("Template Manager")
        self.setMinimumSize(800, 600)
        self.layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("innerTabWidget") # <-- FIX IS HERE
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
        self.layout.addLayout(action_layout)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)
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
        list_widget.addItem(f"New Template {list_widget.count() + 1}")
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