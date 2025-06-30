import json
import os
import random
import re
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QTextEdit, QMessageBox, QDialog, QDialogButtonBox,
                             QListWidget, QTabWidget, QLineEdit, QListWidgetItem)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
import pyperclip

class PasteDetectTextEdit(QTextEdit):
    pasted = pyqtSignal()
    def insertFromMimeData(self, source):
        super().insertFromMimeData(source)
        self.pasted.emit()

class LeadsTab(QWidget):
    output_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.used_templates = []
        self.templates_file = "templates.json"
        self.keywords_file = "keywords.json"
        self.load_templates()
        self.load_keywords()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        self.warning_label = QLabel("Warning: Please double check the generated template!")
        self.warning_label.setTextFormat(Qt.RichText)
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
        manage_keywords_button = QPushButton("Manage Keywords")
        manage_keywords_button.clicked.connect(self.open_keyword_manager)

        button_layout.addWidget(generate_button)
        button_layout.addWidget(manage_templates_button)
        button_layout.addWidget(manage_keywords_button)
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
        for lang, keywords in self.keywords.items():
            if any(word in text_lower for word in keywords):
                return lang
        return "en"

    def select_template(self, language):
        if language in self.templates and self.templates[language]:
             return random.choice(self.templates[language])
        elif "en" in self.templates and self.templates["en"]:
             return random.choice(self.templates["en"])
        return "Template for {language} not found. Client: {client_name}, Machine: {machine_name}"


    def clean_spaces(self, text):
        return re.sub(r'\s+', ' ', text).strip()

    # --- MODIFIED: The parsing logic is now much more robust ---
    def parse_input(self, text, lang):
        # 1. Normalize text: replace different space/newline types
        normalized_text = text.replace('\xa0', ' ').replace('&nbsp;', ' ')
        normalized_text = re.sub(r'(\r\n|\r|\n)', '\n', normalized_text)

        # 2. Define more robust, non-greedy patterns
        patterns = {
            "name": r"Dear\s+([\w\s.'-]+?)\s*,",
            "machine": r"machine:\s*(.*?)(?=\n)", # Non-greedy, stops at the next line break
            "location": r"Location:\s*(.*?)(?=\n)" # Non-greedy, stops at the next line break
        }

        # 3. Find matches
        name_match = re.search(patterns["name"], normalized_text, re.IGNORECASE)
        machine_match = re.search(patterns["machine"], normalized_text, re.IGNORECASE)
        location_match = re.search(patterns["location"], normalized_text, re.IGNORECASE)
        
        # Use findall for links as it's reliable
        links = re.findall(r"https?://\S+", normalized_text)

        # 4. Extract data cleanly
        client_name = name_match.group(1).strip() if name_match else "[Insert client name]"
        machine_name = machine_match.group(1).strip().replace('.', '') if machine_match else "[Insert machine name]"
        location = location_match.group(1).strip() if location_match else "[Insert location]"

        return client_name, machine_name, location, links


    def process_text(self):
        text = self.textbox.toPlainText().strip()
        if not text:
            self.update_status("Please paste some text first.", color="orange")
            return

        lang = self.detect_language(text)
        client_name, machine_name, location, links_found = self.parse_input(text, lang)

        if not links_found:
            self.update_status("Could not find a link in the message.", color="red")
            link_to_use = "[Insert link]"
        else:
            link_to_use = links_found[0]
        
        template = self.select_template(lang)
        final_message = template.format(
            client_name=client_name,
            machine_name=machine_name,
            location=location,
            link=link_to_use
        )

        pyperclip.copy(final_message)
        self.textbox.clear()
        self.update_status("Template generated and copied to clipboard!", color="green")


    def load_templates(self):
        try:
            with open(self.templates_file, 'r', encoding='utf-8') as f:
                self.templates = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.templates = {"en": [], "it": [], "fr": []}
            self.save_templates()
        self.output_message.emit("Templates loaded from JSON file.")

    def save_templates(self):
        with open(self.templates_file, 'w', encoding='utf-8') as f:
            json.dump(self.templates, f, indent=2, ensure_ascii=False)
        self.output_message.emit("Templates saved to JSON file.")

    def open_template_manager(self):
        dialog = TemplateManagerDialog(self.templates, self)
        if dialog.exec_() == QDialog.Accepted:
            self.templates = dialog.get_updated_templates()
            self.save_templates()
            self.update_status("Templates updated successfully.", "green")

    def load_keywords(self):
        try:
            with open(self.keywords_file, 'r', encoding='utf-8') as f:
                self.keywords = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.keywords = {
                "en": [],
                "fr": ["bonjour", "prix", "année", "localisation"],
                "it": ["buongiorno", "gentile", "prezzo", "anno", "località"]
            }
            self.save_keywords()
        self.output_message.emit("Keywords loaded from JSON file.")

    def save_keywords(self):
        with open(self.keywords_file, 'w', encoding='utf-8') as f:
            json.dump(self.keywords, f, indent=2, ensure_ascii=False)
        self.output_message.emit("Keywords saved to JSON file.")

    def open_keyword_manager(self):
        dialog = KeywordManagerDialog(self.keywords, self)
        if dialog.exec_() == QDialog.Accepted:
            self.keywords = dialog.get_updated_keywords()
            self.save_keywords()
            self.update_status("Keywords updated successfully.", "green")


class TemplateManagerDialog(QDialog):
    def __init__(self, templates, parent=None):
        super().__init__(parent)
        self.templates = json.loads(json.dumps(templates))
        self.setWindowTitle("Template Manager")
        self.setMinimumSize(800, 600)
        self.layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
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

class KeywordManagerDialog(QDialog):
    def __init__(self, keywords, parent=None):
        super().__init__(parent)
        self.keywords = json.loads(json.dumps(keywords))
        self.setWindowTitle("Keyword Manager")
        self.setMinimumSize(600, 500)
        self.layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)
        self.keyword_lists = {}
        for lang_code, keyword_list in self.keywords.items():
            lang_tab = QWidget()
            tab_layout = QVBoxLayout(lang_tab)
            list_widget = QListWidget()
            list_widget.addItems(keyword_list)
            self.keyword_lists[lang_code] = list_widget
            tab_layout.addWidget(list_widget)
            controls_layout = QHBoxLayout()
            self.add_keyword_input = QLineEdit()
            self.add_keyword_input.setPlaceholderText("Type new keyword and press Enter...")
            self.add_keyword_input.returnPressed.connect(self.add_keyword)
            add_btn = QPushButton("Add Keyword")
            add_btn.clicked.connect(self.add_keyword)
            remove_btn = QPushButton("Remove Selected")
            remove_btn.clicked.connect(self.remove_keyword)
            controls_layout.addWidget(self.add_keyword_input)
            controls_layout.addWidget(add_btn)
            tab_layout.addLayout(controls_layout)
            tab_layout.addWidget(remove_btn)
            self.tab_widget.addTab(lang_tab, lang_code.upper())
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)
    def get_current_lang_info(self):
        lang_code = self.tab_widget.tabText(self.tab_widget.currentIndex()).lower()
        list_widget = self.keyword_lists[lang_code]
        return lang_code, list_widget
    def add_keyword(self):
        lang_code, list_widget = self.get_current_lang_info()
        keyword = self.add_keyword_input.text().strip().lower()
        if not keyword:
            return
        if keyword not in self.keywords[lang_code]:
            self.keywords[lang_code].append(keyword)
            list_widget.addItem(QListWidgetItem(keyword))
        self.add_keyword_input.clear()
    def remove_keyword(self):
        lang_code, list_widget = self.get_current_lang_info()
        selected_items = list_widget.selectedItems()
        if not selected_items:
            return
        for item in selected_items:
            keyword_to_remove = item.text()
            if keyword_to_remove in self.keywords[lang_code]:
                self.keywords[lang_code].remove(keyword_to_remove)
            list_widget.takeItem(list_widget.row(item))
    def get_updated_keywords(self):
        return self.keywords
