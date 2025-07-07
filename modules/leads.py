import json
import os
import random
import re
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QTextEdit, QMessageBox, QDialog, QDialogButtonBox, 
                             QFormLayout, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
import pyperclip

# Correctly import the class from the 'bots' folder
from bots.leads_bot import AutomationStepper
import pyautogui

class PasteDetectTextEdit(QTextEdit):
    pasted = pyqtSignal()
    def insertFromMimeData(self, source):
        # Anulamos el comportamiento de pegado por defecto para asegurar
        # que SÓLO se inserte texto plano. Esto previene cualquier error
        # al pegar texto enriquecido o HTML.
        if source.hasText():
            # Insertamos manualmente el texto plano del portapapeles
            self.insertPlainText(source.text())

        # Ya no llamamos al método "super" porque hemos gestionado el pegado nosotros mismos.

        # Emitimos la señal para iniciar la lógica de procesamiento
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

    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.bot_window = None # To hold a reference to the bot window
        self.used_templates = []
        self.templates_file = "templates/leads_templates.json"
        self.rules_file = "regex/parsing_rules.json"
        self.template_counter = 0
        self.load_templates()
        self.load_rules()
        self.init_ui()
        self.update_counter_display()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # --- Top Section Layout ---
        top_layout = QHBoxLayout()
        
        info_layout = QVBoxLayout()
        self.warning_label = QLabel("Warning: Please double check the generated template!")
        self.warning_label.setStyleSheet("font-weight: bold; color: orange;")
        title_label = QLabel("Paste the client message below and click 'Generate Template'")
        info_layout.addWidget(self.warning_label)
        info_layout.addWidget(title_label)
        
        # NEW: Create and style the counter label
        self.counter_label = QLabel()
        self.counter_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.counter_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        top_layout.addLayout(info_layout)
        top_layout.addWidget(self.counter_label)
        
        main_layout.addLayout(top_layout)
        # --- End of Top Section Layout ---

        self.textbox = PasteDetectTextEdit()
        self.textbox.pasted.connect(self.on_paste)
        self.textbox.setPlaceholderText("Paste client message here...")
        main_layout.addWidget(self.textbox)

        button_layout = QHBoxLayout()
        generate_button = QPushButton("Generate Template")
        generate_button.clicked.connect(self.process_text)

        launch_bot_button = QPushButton("Launch Leads Bot")
        launch_bot_button.clicked.connect(self.launch_leads_bot)

        button_layout.addWidget(generate_button)
        button_layout.addWidget(launch_bot_button)

        main_layout.addLayout(button_layout)
        self.status_label = QLabel("")
        main_layout.addWidget(self.status_label)

    def launch_leads_bot(self):
        """Creates and shows the AutomationStepper window after a warning."""
        # If the bot window already exists, just show it and bring it to the front
        if self.bot_window and self.bot_window.isVisible():
            self.bot_window.activateWindow()
            self.bot_window.raise_()
            return

        # --- ADDED SECTION ---
        # 1. Get screen size information
        reference_width = 1920
        reference_height = 1080
        screen_width, screen_height = pyautogui.size()

        # 2. Create the warning message
        warning_message = (
            "CRITICAL INFORMATION:\n\n"
            "THIS SCRIPT MUST BE USED WITH A FIREFOX BROWSER AT 80% OF ZOOM + SPLIT VIEW\n\n"
            "THE LEADS MUST BE IN INDEX-VIEW(NOT TABLE VIEW)\n\n"
            f"Reference screen size: {reference_width}x{reference_height}\n"
            f"Current screen size: {screen_width}x{screen_height}"
        )

        # 3. Show the warning pop-up and check the user's response
        reply = QMessageBox.warning(self, "Bot Prerequisites", warning_message,
                                    QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)

        # 4. If user clicks Cancel, stop before creating the window
        if reply == QMessageBox.Cancel:
            self.update_status("Bot launch cancelled by user.", color="orange")
            return
        # --- END OF ADDED SECTION ---

        self.update_status("Launching Leads Bot...", color="green")

        # Create an instance of the bot window
        self.bot_window = AutomationStepper()

        # Apply dark mode if the main app is in dark mode
        if self.main_window and self.main_window.is_dark_mode:
            self.bot_window.apply_dark_mode_stylesheet()

        self.bot_window.show()
        self.output_message.emit("Leads Bot launched successfully as a new window.\n")

    def on_paste(self):
        QTimer.singleShot(50, self.process_text)

    def update_status(self, message, color="black"):
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color};")
        self.output_message.emit(f"[Leads Tab] {message.splitlines()[0]}...\n")

    def detect_language(self, text):
        text_lower = text.lower()
        for rule in self.rules:
            if rule.get('type') == 'language_detect':
                if re.search(rule.get('pattern', ''), text_lower, re.IGNORECASE):
                    return rule.get('value')
        return "en"

    def parse_input(self, text):
        results = {"name": "", "machine": "", "location": "", "link": ""}
        for rule in self.rules:
            if rule.get('type') == 'extraction':
                field = rule.get('value')
                pattern = rule.get('pattern')
                if field and pattern and not results.get(field):
                    try:
                        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                        if match and match.groups():
                            results[field] = match.group(1).strip().rstrip('.')
                    except re.error as e:
                        print(f"Regex error in rule '{rule.get('name')}': {e}")
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
        self.template_counter += 1
        self.update_counter_display()
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
            
    def load_templates(self):
        try:
            with open(self.templates_file, 'r', encoding='utf-8') as f:
                self.templates = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.templates = {"en": ["Hello {client_name}, ..."], "it": [], "fr": []}
            self.save_templates()

    def update_counter_display(self):
        """Updates the text of the counter label in the UI."""
        self.counter_label.setText(f"Templates Generated: {self.template_counter}")
