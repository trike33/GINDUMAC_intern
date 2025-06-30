import sys
import os
import csv
import re
import random
from datetime import datetime
from log_tab import LogTab

# Import PyQt5 modules
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QMessageBox, QFileDialog,
    QLineEdit, QProgressBar, QTabWidget, QFrame,
    QGroupBox, QGridLayout, QGraphicsDropShadowEffect, QSizePolicy, QTextEdit
)
from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal, pyqtSlot, QTimer
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPainter, QColor, QPen
import random

# Ensure pyperclip is installed
try:
    import pyperclip
except ImportError:
    # This is a fallback for command-line execution if pyperclip is missing.
    # The main GUI has its own check.
    print("Error: pyperclip not found. Please install it using 'pip install pyperclip'")
    sys.exit(1)

class PasteDetectTextEdit(QTextEdit):
    pasted = pyqtSignal()

    def insertFromMimeData(self, source):
        super().insertFromMimeData(source)
        self.pasted.emit()

# -----------------------------------------------------------------------------
# LOGIC FROM email_generator_logic.py
# -----------------------------------------------------------------------------

# Email templates for leads
LEAD_TEMPLATES = {
    "en": """Dear {name}

I hope you're doing well. I'm reaching out to follow up on your earlier 
interest in the {machine} we discussed at the price of {price}. {link}

Are you still considering this machine? We need to find a client in the 
next 2 weeks, so we are open to discounts and counteroffers.

If you are still interested let me know or send me your best offer, 
please.

Best Regards,""",
    
    "it": """Caro {name}

Spero che tu stia bene. Ti scrivo per riprendere il contatto in merito al 
tuo interesse per la MACCHINA {machine} di cui abbiamo parlato al prezzo 
di {price}. {link}

Sei ancora interessato a questa macchina? Dobbiamo trovare un acquirente 
entro le prossime due settimane, quindi siamo aperti a sconti e 
controfferte.

Se sei ancora interessato, fammi sapere o inviami la tua migliore offerta, 
per favore.

Cordiali saluti""",

    "fr": """Cher {name}

J’espère que vous allez bien. Je me permets de revenir vers vous 
concernant votre intérêt pour la MACHINE {machine} dont nous avons parlé 
au prix de {price}. {link}

Êtes-vous toujours intéressé par cette machine ? Nous devons trouver un 
acheteur dans les deux prochaines semaines, donc nous sommes ouverts aux 
remises et contre-propositions.

Si vous êtes toujours intéressé, merci de me le faire savoir ou de 
m’envoyer votre meilleure offre.

Cordialement"""
}

# Country to language mapping for leads
LEAD_COUNTRY_LANG_MAP = {
    'Italy': 'it',
    'France': 'fr',
    'Belgium': 'fr',
    'Switzerland': 'fr',
    'Canada': 'fr',
    'USA': 'en',
    'United States': 'en',
    'UK': 'en',
    'Germany': 'en',
    'Spain': 'en',
}

def get_lead_email_generator(csv_path, price, link, machine):
    """
    Generator function to yield one lead email at a time.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"File not found: {csv_path}")

    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader) # Read all rows into memory to get total count
        total_rows = len(rows)

        for i, row in enumerate(rows):
            if not all(k in row for k in ['Lead Email', 'Lead Country']):
                # Skip row if essential keys are missing
                continue 
                
            email = row.get('Lead Email', '').strip()
            country = row.get('Lead Country', '').strip()

            if not email or not country:
                continue

            # Language logic
            language = LEAD_COUNTRY_LANG_MAP.get(country, 'en')
            template = LEAD_TEMPLATES[language]

            # Extract first part of name (e.g., john.doe@example.com → John)
            name_part = email.split('@')[0].split('.')[0]
            name = name_part.capitalize()

            # Fill in template
            filled_email = template.format(name=name, machine=machine, price=price, link=link)

            yield {
                "email": email,
                "country": country,
                "language": language,
                "message": filled_email,
                "progress_current": i + 1,
                "progress_total": total_rows
            }


# -----------------------------------------------------------------------------
# LOGIC FROM seller_followup_logic.py
# -----------------------------------------------------------------------------

# Templates with placeholders for sellers
SELLER_TEMPLATES = {
    "en": """Dear {name},

I hope you're doing well.

Some time ago, we had the opportunity to advertise some of your machines on our platform. I’m reaching out to ask if you currently have any machines for sale.

If so, please feel free to send me the details. We’d be happy to help you find potential buyers.

Best regards,""",
    
    "fr": """Cher {name},

J’espère que vous allez bien.

Il y a quelque temps, nous avons eu l’occasion de promouvoir certaines de vos machines sur notre plateforme. Je me permets de vous demander si vous avez actuellement des machines à vendre.

Si c’est le cas, n’hésitez pas à m’envoyer les détails. Nous serions ravis de vous aider à trouver des acheteurs potentiels.

Cordialement,""",
    
    "it": """Caro {name},

Spero che tu stia bene.

Qualche tempo fa abbiamo avuto l’opportunità di pubblicizzare alcune delle tue macchine sulla nostra piattaforma. Ti contatto per sapere se attualmente hai delle macchine in vendita.

Se sì, sentiti libero di inviarmi i dettagli. Saremo felici di aiutarti a trovare potenziali acquirenti.

Cordiali saluti,"""
}

# Country to language mapping for sellers
SELLER_COUNTRY_LANG_MAP = {
    'Italy': 'it',
    'France': 'fr',
    'Belgium': 'fr',
    'Switzerland': 'fr',
    'Canada': 'fr',
    'USA': 'en',
    'United States': 'en',
    'UK': 'en',
    'Germany': 'en',
    'Spain': 'en',
}

# Countries to skip for seller follow-up
EXCLUDED_COUNTRIES = {
    "australia", "belarus", "brazil", "egypt", "germany", "india", "indonesia",
    "israel", "jordan", "korea republic of", "kuwait", "mexico", "moroco", "pakistan",
    "turkey", "ukraine", "united arab emirates", "united states"
}


def extract_name(email):
    if '@' not in email:
        return "Client"
    return email.split('@')[0].split('.')[0].capitalize()

def get_seller_followup_email_generator(csv_path, start_email_str=None):
    """
    Generator function to yield one seller follow-up email at a time.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"File not found: {csv_path}")

    start_output = False if start_email_str else True
    
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)
        total_rows = len(rows)

        if start_email_str:
            start_email_str_lower = start_email_str.lower()

        for i, row in enumerate(rows):
            row_index = i + 2 # +1 for 0-index, +1 for header row in CSV
            email = row.get('Email address', '').strip()
            country = row.get('Country', '').strip().lower()

            if start_email_str and not start_output:
                if email.lower() == start_email_str_lower:
                    start_output = True
                else:
                    continue 

            if not start_output:
                continue

            if country in EXCLUDED_COUNTRIES:
                continue

            name = extract_name(email)
            lang = SELLER_COUNTRY_LANG_MAP.get(country.title(), 'en')
            template = SELLER_TEMPLATES[lang]

            message = template.format(name=name)
            
            yield {
                "row_index": row_index,
                "email": email,
                "country": country,
                "language": lang,
                "message": message,
                "progress_current": i + 1,
                "progress_total": total_rows
            }


# -----------------------------------------------------------------------------
# PYQT5 APPLICATION
# -----------------------------------------------------------------------------

# --- Worker for threading background tasks ---
class Worker(QObject):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(tuple)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            generator = self.func(*self.args, **self.kwargs)
            # A worker for a generator should just return the generator object
            self.finished.emit(generator)
        except Exception as e:
            self.error.emit(str(e))

# --- Leads Template Tab ---
class LeadsTab(QWidget):
    output_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.used_templates = []

        self.templates = {
            "en": [
                """Hello {client_name},
Did you have time to consider the offer related to the machine {machine_name} that we have in {location}? {link}
Let me know if you need any additional information.""",
                """Hello {client_name},
Are you still interested in machine {machine_name} that we have in {location}? {link}
Do you need any further information?""",
                """Hello {client_name},
Did you have time to consider the offer related to machine {machine_name} that we have in {location}? {link}
Do you need any additional information?""",
                """Hello {client_name},
Are you still interested in the offer related to machine {machine_name} that we have in {location}? {link}
Let me know if you need any additional information."""
            ],
            "it": [
                """Buongiorno {client_name},
Hai avuto tempo sufficiente per considerare la mia offerta per la macchina {machine_name} che abbiamo in {location}? {link}
Hai bisogno di ulteriori informazione? Sei ancora interessato?"""
            ],
            "fr": [
                """Bonjour {client_name},
Avez-vous eu le temps de considérer l'offre relative à la machine {machine_name} que nous avons en {location}? {link}
N'hésitez pas à me contacter si vous avez besoin d'informations supplémentaires."""
            ]
        }
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        title_label = QLabel("📋 Paste the client message below and click 'Generate Template'")
        title_label.setFont(self.font_for_size(12, bold=True))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        self.textbox = PasteDetectTextEdit()
        self.textbox.pasted.connect(self.on_paste)
        self.textbox.setPlaceholderText("Paste client message here to instantly generate the template from it...")
        self.textbox.setMinimumSize(600, 250)
        self.textbox.setFont(self.font_for_size(11, family="Consolas"))
        main_layout.addWidget(self.textbox)

        generate_button = QPushButton("🚀 Generate Template")
        generate_button.setFont(self.font_for_size(12, bold=True))
        generate_button.setFixedSize(200, 40)
        generate_button.clicked.connect(self.process_text)
        main_layout.addWidget(generate_button, alignment=Qt.AlignCenter)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.status_label.setFont(self.font_for_size(11))
        self.status_label.setMinimumHeight(60)
        main_layout.addWidget(self.status_label)

    def on_paste(self):
        QTimer.singleShot(50, self.process_text)

    def font_for_size(self, size, family="Arial", bold=False):
        font = self.font()
        font.setPointSize(size)
        font.setFamily(family)
        font.setBold(bold)
        return font

    def update_status(self, message, color="black"):
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color};")
        self.output_message.emit(f"[Leads Tab] {message.splitlines()[0]}...")

    def detect_language(self, text):
        text_lower = text.lower()
        if any(word in text_lower for word in ["bonjour", "prix", "année", "localisation"]): return "fr"
        if any(word in text_lower for word in ["buongiorno", "gentile", "prezzo", "anno", "località"]): return "it"
        return "en"

    def select_template(self, language):
        if language == "en":
            available = [i for i in range(len(self.templates["en"])) if i not in self.used_templates]
            if not available:
                self.used_templates = []
                available = list(range(len(self.templates["en"])))
            chosen = random.choice(available)
            self.used_templates.append(chosen)
            return self.templates["en"][chosen]
        return self.templates[language][0]

    def clean_spaces(self, text):
        return re.sub(r'\s+', ' ', text).strip()

    def parse_input(self, text, lang):
        patterns = {
            "name": {
                "en": r"(Dear|Hello|Hi)\s+([A-Za-z\s]+?)[,\n]",
                "it": r"(Gentile|Ciao)\s+([A-Za-z\s]+?)[,\n]",
                "fr": r"(Bonjour|Cher)\s+([A-Za-z\s]+?)[,\n]"
            },
            "machine": r"(?:machine|macchina|MACHINE):\s*([^\n]+)",
            "location": r"(?:Location|Località|Localisation):\s*([^\n]+)",
            "link": r"https?://\S+"
        }
        
        name = re.search(patterns["name"].get(lang, patterns["name"]["en"]), text, re.IGNORECASE)
        machine = re.search(patterns["machine"], text, re.IGNORECASE)
        location = re.search(patterns["location"], text, re.IGNORECASE)
        link = re.search(patterns["link"], text)

        return (
            self.clean_spaces(name.group(2)) if name else "[Insert client name]",
            self.clean_spaces(machine.group(1)) if machine else "[Insert machine name]",
            self.clean_spaces(location.group(1)) if location else "[Insert location]",
            link.group(0).strip() if link else "[Insert link]"
        )

    def process_text(self):
        text = self.textbox.toPlainText().strip()
        if not text:
            self.update_status("⚠️ Please paste some text first.", color="orange")
            return

        lang = self.detect_language(text)
        template = self.select_template(lang)
        client_name, machine_name, location, link = self.parse_input(text, lang)

        final_message = template.format(client_name=client_name, machine_name=machine_name, location=location, link=link)
        pyperclip.copy(final_message)
        self.textbox.clear()
        self.update_status(f"✅ Template copied to clipboard:\n\n📩 {final_message}", color="green")


# --- Email Sent (Leads) Tab ---
class EmailSentTab(QWidget):
    output_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.templates = {
            "English": "Hello,\n\nDid you get my offer? Are you still interested?",
            "Italian": "Ciao,\n\nHai ricevuto la mia offerta? Sei ancora interessato?",
            "French": "Bonjour,\n\nAvez-vous reçu mon offre ? Êtes-vous toujours intéressé ?"
        }
        self.click_counts = {"English": 0, "Italian": 0, "French": 0}
        self.timestamp_written = False
        self.URLS_FILE = "urls.txt"
        self.init_ui()
        self.load_url_preview()
        self.update_counters()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # --- Buttons and Counters ---
        btn_frame = QGroupBox("Select Language to Copy Template")
        btn_frame.setFont(self.font_for_size(12, bold=True))
        btn_layout = QGridLayout(btn_frame)
        btn_layout.setSpacing(10)
        
        lang_data = [("🇬🇧 English", "English"), ("🇮🇹 Italian", "Italian"), ("🇫🇷 French", "French")]
        self.count_labels = {}
        for i, (text, lang) in enumerate(lang_data):
            button = QPushButton(text)
            button.setFont(self.font_for_size(10, bold=True))
            button.setFixedSize(120, 35)
            button.clicked.connect(lambda _, l=lang: self.copy_template(l))
            
            self.count_labels[lang] = QLabel(f"{lang} clicks: 0")
            self.count_labels[lang].setFont(self.font_for_size(10))
            
            btn_layout.addWidget(button, i, 0, alignment=Qt.AlignCenter)
            btn_layout.addWidget(self.count_labels[lang], i, 1, alignment=Qt.AlignLeft)

        main_layout.addWidget(btn_frame, alignment=Qt.AlignCenter)

        self.total_count_lbl = QLabel("Total clicks: 0")
        self.total_count_lbl.setFont(self.font_for_size(12, bold=True))
        self.total_count_lbl.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.total_count_lbl)

        self.status_label = QLabel("Click a button to copy the template.")
        self.status_label.setFont(self.font_for_size(12))
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)
        main_layout.addSpacing(20)

        # --- URL Management ---
        url_group = QGroupBox("URL Management")
        url_group.setFont(self.font_for_size(12, bold=True))
        url_layout = QVBoxLayout(url_group)

        url_layout.addWidget(QLabel("Enter URLs below (one per line):"))
        self.url_textbox = QTextEdit()
        self.url_textbox.setFixedSize(500, 100)
        self.url_textbox.setFont(self.font_for_size(12))
        url_layout.addWidget(self.url_textbox)

        save_urls_button = QPushButton("Save URLs to File")
        save_urls_button.clicked.connect(self.save_urls)
        url_layout.addWidget(save_urls_button, alignment=Qt.AlignCenter)
        url_layout.addSpacing(10)

        url_layout.addWidget(QLabel("Saved URLs Preview:"))
        self.url_preview_text = QTextEdit()
        self.url_preview_text.setReadOnly(True)
        self.url_preview_text.setFont(self.font_for_size(10, family="Consolas"))
        self.url_preview_text.setFixedSize(500, 150)
        url_layout.addWidget(self.url_preview_text)
        main_layout.addWidget(url_group, alignment=Qt.AlignCenter)
        main_layout.addStretch(1)

    def font_for_size(self, size, family="Helvetica", bold=False):
        font = self.font()
        font.setPointSize(size)
        font.setFamily(family)
        font.setBold(bold)
        return font

    def copy_template(self, lang):
        pyperclip.copy(self.templates[lang])
        self.click_counts[lang] += 1
        self.update_status(f"✅ {lang} template copied to clipboard!")
        self.update_counters()
        self.output_message.emit(f"[Email Sent Tab] Copied {lang} template.\n")

    def update_counters(self):
        for lang, label in self.count_labels.items():
            label.setText(f"{lang} clicks: {self.click_counts[lang]}")
        self.total_count_lbl.setText(f"Total clicks: {sum(self.click_counts.values())}")

    def update_status(self, message):
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: green;" if "✅" in message else "color: black;")

    def save_urls(self):
        content = self.url_textbox.toPlainText().strip()
        if not content:
            self.update_status("⚠️ No URLs to save.")
            self.status_label.setStyleSheet("color: orange;")
            return

        try:
            with open(self.URLS_FILE, "a", encoding="utf-8") as f:
                if not self.timestamp_written:
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"\n\n--- Session started at {now} ---\n")
                    self.timestamp_written = True
                f.write(content + "\n")
            self.update_status("💾 URLs saved successfully.")
            self.url_textbox.clear()
            self.load_url_preview()
            self.output_message.emit(f"[Email Sent Tab] URLs saved to {self.URLS_FILE}\n")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save URLs:\n{e}")
            self.output_message.emit(f"[Email Sent Tab] Error saving URLs: {e}\n")

    def load_url_preview(self):
        if not os.path.exists(self.URLS_FILE):
            preview_text = "(No URLs saved yet)"
        else:
            try:
                with open(self.URLS_FILE, "r", encoding="utf-8") as f:
                    preview_text = f.read().strip()
                if not preview_text:
                    preview_text = "(File is empty)"
            except Exception as e:
                preview_text = f"(Error reading file: {e})"
        self.url_preview_text.setText(preview_text)


# --- Seller Follow-up Tab ---
class SellerFollowupTab(QWidget):
    output_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.email_generator_obj = None
        self.current_email_data = None
        self.thread = None
        self.worker = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        csv_frame = QGroupBox("CSV File Selection")
        csv_layout = QGridLayout(csv_frame)
        self.csv_path_qle = QLineEdit()
        self.start_email_qle = QLineEdit()
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_csv)
        csv_layout.addWidget(QLabel("CSV File:"), 0, 0)
        csv_layout.addWidget(self.csv_path_qle, 0, 1)
        csv_layout.addWidget(browse_button, 0, 2)
        csv_layout.addWidget(QLabel("Start Email (optional):"), 1, 0)
        csv_layout.addWidget(self.start_email_qle, 1, 1, 1, 2)
        main_layout.addWidget(csv_frame)

        button_layout = QHBoxLayout()
        self.initialize_button = QPushButton("Initialize Process")
        self.initialize_button.clicked.connect(self.initialize_process)
        self.copy_next_button = QPushButton("Copy Next Email")
        self.copy_next_button.clicked.connect(self.copy_next_email)
        self.reset_button = QPushButton("Reset Process")
        self.reset_button.clicked.connect(self.reset_process)
        button_layout.addWidget(self.initialize_button)
        button_layout.addWidget(self.copy_next_button)
        button_layout.addWidget(self.reset_button)
        main_layout.addLayout(button_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_label = QLabel("Progress: 0/0 (0%)")
        self.current_info_label = QLabel("Current Email: ")
        self.email_display_text = QTextEdit()
        self.email_display_text.setReadOnly(True)
        # Use a cross-platform monospace font
        self.email_display_text.setFont(self.font_for_size(10, family="Courier"))
        main_layout.addWidget(self.progress_label)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.current_info_label)
        main_layout.addWidget(QLabel("Generated Email Content:"))
        main_layout.addWidget(self.email_display_text)
        main_layout.addStretch(1)

        self.reset_process()

    def font_for_size(self, size, family="Arial", bold=False):
        font = self.font()
        font.setPointSize(size)
        font.setFamily(family)
        font.setBold(bold)
        return font

    def browse_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV files (*.csv)")
        if file_path:
            self.csv_path_qle.setText(file_path)

    def initialize_process(self):
        csv_path = self.csv_path_qle.text()
        if not csv_path or not os.path.exists(csv_path):
            QMessageBox.warning(self, "Input Error", "Please select a valid CSV file.")
            return

        self.initialize_button.setEnabled(False)
        self.output_message.emit("[Seller Follow-up] Initializing...\n")
        
        start_email = self.start_email_qle.text().strip()
        self.thread = QThread()
        self.worker = Worker(get_seller_followup_email_generator, csv_path, start_email or None)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.error.connect(self.on_worker_error)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.start()

    @pyqtSlot(object)
    def on_worker_finished(self, generator):
        self.email_generator_obj = generator
        self.copy_next_button.setEnabled(True)
        self.reset_button.setEnabled(True)
        start_msg = f"from '{self.start_email_qle.text()}'" if self.start_email_qle.text() else "from beginning"
        self.output_message.emit(f"[{self.windowTitle()}] Initialized successfully {start_msg}.\n")
        self.current_info_label.setText("Ready. Click 'Copy Next Email'.")

    @pyqtSlot(str)
    def on_worker_error(self, error_msg):
        QMessageBox.critical(self, "Error", f"An error occurred: {error_msg}")
        self.output_message.emit(f"[{self.windowTitle()}] Error: {error_msg}\n")
        self.reset_process()

    def copy_next_email(self):
        if not self.email_generator_obj:
            return
        try:
            data = next(self.email_generator_obj)
            pyperclip.copy(data["message"])
            self.email_display_text.setText(data["message"])

            # *** THIS IS THE FIX ***
            # Check if 'row_index' exists before trying to display it.
            if 'row_index' in data:
                info = f"Row {data['row_index']} | Email: {data['email']}"
            else:
                info = f"Email: {data['email']}"

            self.current_info_label.setText(f"Current: {info}")
            self.update_progress(data['progress_current'], data['progress_total'])
            self.output_message.emit(f"[{self.windowTitle()}] Copied email for {data['email']}.\n")
        except StopIteration:
            QMessageBox.information(self, "Complete", "All eligible emails processed.")
            self.output_message.emit(f"[{self.windowTitle()}] Process complete.\n")
            self.reset_process()
            self.current_info_label.setText("Processing Complete.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process next email: {e}")
            self.reset_process()

    def reset_process(self):
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        self.email_generator_obj = None
        self.initialize_button.setEnabled(True)
        self.copy_next_button.setEnabled(False)
        self.reset_button.setEnabled(False)
        self.email_display_text.clear()
        self.current_info_label.setText("Process reset. Select inputs to initialize.")
        self.update_progress(0, 0)
        # Check if the widget is visible before emitting a signal
        if self.isVisible():
            self.output_message.emit(f"[{self.windowTitle()}] Process reset.\n")


    def update_progress(self, current, total):
        if total > 0:
            percent = int((current / total) * 100)
            self.progress_bar.setValue(percent)
            self.progress_label.setText(f"Progress: {current}/{total} ({percent}%)")
        else:
            self.progress_bar.setValue(0)
            self.progress_label.setText("Progress: 0/0 (0%)")

# --- Email Generator (Metabase) Tab ---
class EmailGeneratorTab(QWidget):
    output_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.email_generator_obj = None
        self.thread = None
        self.worker = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        input_frame = QGroupBox("Machine Details & CSV")
        input_layout = QGridLayout(input_frame)
        self.machine_price_qle = QLineEdit()
        self.machine_link_qle = QLineEdit()
        self.machine_name_qle = QLineEdit()
        self.csv_path_qle = QLineEdit()
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_csv)
        
        input_layout.addWidget(QLabel("Machine Price:"), 0, 0)
        input_layout.addWidget(self.machine_price_qle, 0, 1)
        input_layout.addWidget(QLabel("Machine Link:"), 1, 0)
        input_layout.addWidget(self.machine_link_qle, 1, 1)
        input_layout.addWidget(QLabel("Machine Name:"), 2, 0)
        input_layout.addWidget(self.machine_name_qle, 2, 1)
        input_layout.addWidget(QLabel("CSV File:"), 3, 0)
        input_layout.addWidget(self.csv_path_qle, 3, 1)
        input_layout.addWidget(browse_button, 3, 2)
        main_layout.addWidget(input_frame)

        button_layout = QHBoxLayout()
        self.initialize_button = QPushButton("Initialize Process")
        self.initialize_button.clicked.connect(self.initialize_process)
        self.copy_next_button = QPushButton("Copy Next Email")
        self.copy_next_button.clicked.connect(self.copy_next_email)
        self.reset_button = QPushButton("Reset Process")
        self.reset_button.clicked.connect(self.reset_process)
        button_layout.addWidget(self.initialize_button)
        button_layout.addWidget(self.copy_next_button)
        button_layout.addWidget(self.reset_button)
        main_layout.addLayout(button_layout)

        self.progress_bar = QProgressBar()
        self.progress_label = QLabel("Progress: 0/0 (0%)")
        self.current_info_label = QLabel("Current Email: ")
        self.email_display_text = QTextEdit()
        self.email_display_text.setReadOnly(True)
        self.email_display_text.setFont(self.font_for_size(10, family="Consolas"))
        main_layout.addWidget(self.progress_label)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.current_info_label)
        main_layout.addWidget(QLabel("Generated Email Content:"))
        main_layout.addWidget(self.email_display_text)
        main_layout.addStretch(1)

        self.reset_process()

    def browse_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV files (*.csv)")
        if file_path:
            self.csv_path_qle.setText(file_path)

    def initialize_process(self):
        csv = self.csv_path_qle.text()
        price = self.machine_price_qle.text()
        link = self.machine_link_qle.text()
        name = self.machine_name_qle.text()

        if not all([csv, price, link, name]) or not os.path.exists(csv):
            QMessageBox.warning(self, "Input Error", "Please fill all fields and select a valid CSV.")
            return

        self.initialize_button.setEnabled(False)
        self.output_message.emit("[Email Generator] Initializing...\n")
        
        self.thread = QThread()
        self.worker = Worker(get_lead_email_generator, csv, price, link, name)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.error.connect(self.on_worker_error)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.start()

    @pyqtSlot(object)
    def on_worker_finished(self, generator):
        self.email_generator_obj = generator
        self.copy_next_button.setEnabled(True)
        self.reset_button.setEnabled(True)
        self.output_message.emit(f"[Email Generator] Initialized for '{self.machine_name_qle.text()}'.\n")
        self.current_info_label.setText("Ready. Click 'Copy Next Email'.")

    @pyqtSlot(str)
    def on_worker_error(self, error_msg):
        QMessageBox.critical(self, "Error", f"An error occurred: {error_msg}")
        self.output_message.emit(f"[Email Generator] Error: {error_msg}\n")
        self.reset_process()
    
    # Re-using the same logic for copy/reset/progress as SellerFollowupTab
    copy_next_email = SellerFollowupTab.copy_next_email
    reset_process = SellerFollowupTab.reset_process
    update_progress = SellerFollowupTab.update_progress
    font_for_size = SellerFollowupTab.font_for_size

class WelcomeWindow(QMainWindow):
    def __init__(self, main_window=None):
        super().__init__()
        self.setWindowTitle("Welcome to GINDUMAC")
        self.setGeometry(200, 150, 900, 600)
        self.main_window = main_window
        self.setAttribute(Qt.WA_OpaquePaintEvent)

        self.init_animation()
        self.init_ui()

        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update)
        self.animation_timer.start(30)

    def init_ui(self):
        # Main container
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(Qt.AlignCenter)

        # Foreground container
        content_box = QWidget()
        content_box.setStyleSheet("background-color: rgba(255,255,255,0.85); border-radius: 12px;")
        content_layout = QVBoxLayout(content_box)
        content_layout.setAlignment(Qt.AlignCenter)
        content_layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("Welcome to Our GINDUMAC Intern Application!")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2c3e50;")

        subtitle = QLabel(
            "We're excited to have you here.\n"
            "This app is designed to help you manage tasks efficiently and collaborate seamlessly.\n"
            "Explore its features and streamline your workflow."
        )
        subtitle.setFont(QFont("Segoe UI", 14))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #34495e;")

        self.start_button = QPushButton("Get Started")
        self.start_button.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.start_button.setCursor(Qt.PointingHandCursor)
        self.start_button.setFixedSize(180, 40)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton:pressed { background-color: #21618c; }
        """)
        self.start_button.clicked.connect(self.on_get_started_clicked)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(2, 2)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.start_button.setGraphicsEffect(shadow)

        content_layout.addWidget(title)
        content_layout.addSpacing(10)
        content_layout.addWidget(subtitle)
        content_layout.addSpacing(30)
        content_layout.addWidget(self.start_button, alignment=Qt.AlignCenter)

        self.layout.addStretch()
        self.layout.addWidget(content_box, alignment=Qt.AlignCenter)
        self.layout.addStretch()

    def init_animation(self):
        self.shapes = []
        self.shape_min_size = 20
        self.shape_max_size = 60
        self.num_shapes = 10

        for _ in range(self.num_shapes):
            self.create_random_shape()

    def create_random_shape(self):
        size = random.randint(self.shape_min_size, self.shape_max_size)
        x = random.randint(0, self.width() or 900 - size)
        y = random.randint(0, self.height() or 600 - size)
        color = QColor(random.randint(50, 200), random.randint(50, 200), random.randint(50, 200), 130)
        vx = random.choice([-2, -1, 1, 2])
        vy = random.choice([-2, -1, 1, 2])
        shape_type = random.choice(["circle", "square"])

        self.shapes.append({
            'x': x, 'y': y, 'size': size, 'color': color,
            'vx': vx, 'vy': vy, 'type': shape_type
        })

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#f0f4f8"))

        for shape in self.shapes:
            shape['x'] += shape['vx']
            shape['y'] += shape['vy']

            if shape['x'] <= 0 or shape['x'] + shape['size'] >= self.width():
                shape['vx'] *= -1
            if shape['y'] <= 0 or shape['y'] + shape['size'] >= self.height():
                shape['vy'] *= -1

            painter.setBrush(shape['color'])
            painter.setPen(Qt.NoPen)

            if shape['type'] == 'circle':
                painter.drawEllipse(shape['x'], shape['y'], shape['size'], shape['size'])
            else:
                painter.drawRect(shape['x'], shape['y'], shape['size'], shape['size'])

    def on_get_started_clicked(self):
        self.close()
        if self.main_window:
            self.main_window.notebook.setCurrentIndex(0)


# --- Main Application Window ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Integrated Email Tools")
        self.setGeometry(100, 100, 900, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Header with logo and welcome button
        logo_frame = QFrame()
        logo_frame.setStyleSheet("background-color: #003366;")
        logo_layout = QHBoxLayout(logo_frame)
        logo_layout.setContentsMargins(10, 5, 10, 5)

        # GINDUMAC label (aligned left)
        gindumac_label = QLabel("GINDUMAC GMBH ®")
        gindumac_label.setFont(self.font_for_size(24, family="Helvetica", bold=True))
        gindumac_label.setStyleSheet("color: white; padding: 10px;")
        gindumac_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # Spacer
        logo_spacer = QWidget()
        logo_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # Welcome Button (aligned right)
        welcome_button = QPushButton("🏠 Welcome")
        welcome_button.setCursor(Qt.PointingHandCursor)
        welcome_button.setFixedSize(130, 35)
        welcome_button.clicked.connect(self.open_welcome_window)
        welcome_button.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #003366;
                font-weight: bold;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #eeeeee; }
            QPushButton:pressed { background-color: #dddddd; }
        """)

        # Assemble header
        logo_layout.addWidget(gindumac_label)
        logo_layout.addWidget(logo_spacer)
        logo_layout.addWidget(welcome_button)
        main_layout.addWidget(logo_frame)


        # Tabs
        self.notebook = QTabWidget()
        main_layout.addWidget(self.notebook)
        
        # Add tabs and connect their output signals
        tabs = {
            "Leads Template": LeadsTab,
            "Leads I-sent": EmailSentTab,
            "Contacts": SellerFollowupTab,
            "Metabase": EmailGeneratorTab,
            "📜 Temporal Logs": LogTab
        }
        for name, TabClass in tabs.items():
            tab = TabClass(self.notebook)
            # Check if the tab has the output_message signal before connecting
            if hasattr(tab, 'output_message'):
                tab.output_message.connect(self.insert_output)
            self.notebook.addTab(tab, name)

        # Output Console
        output_group_box = QGroupBox("Application Output")
        output_layout = QVBoxLayout(output_group_box)
        self.output_text_edit = QTextEdit()
        self.output_text_edit.setReadOnly(True)
        # Fix for the font warning: Use a cross-platform monospace font
        self.output_text_edit.setFont(self.font_for_size(10, family="Courier"))
        output_layout.addWidget(self.output_text_edit)
        main_layout.addWidget(output_group_box)
        main_layout.setStretchFactor(self.notebook, 3)
        main_layout.setStretchFactor(output_group_box, 1)

        self.insert_output("Welcome to the Integrated Email Tools!\n" + "="*70 + "\n")
        self.apply_stylesheet()

    def font_for_size(self, size, family="Arial", bold=False):
        font = self.font()
        font.setPointSize(size)
        font.setFamily(family)
        font.setBold(bold)
        return font

    def open_welcome_window(self):
        # Avoid multiple windows stacking
        if hasattr(self, 'welcome_win') and self.welcome_win.isVisible():
            self.welcome_win.raise_()
            self.welcome_win.activateWindow()
            return
        self.welcome_win = WelcomeWindow(main_window=self)
        self.welcome_win.show()

    @pyqtSlot(str)
    def insert_output(self, message):
        """Appends a message to the central output console."""
        self.output_text_edit.moveCursor(self.output_text_edit.textCursor().End)
        self.output_text_edit.insertPlainText(message)
        self.output_text_edit.ensureCursorVisible()

    def apply_stylesheet(self):
        # Using a more robust selector for the output console
        self.output_text_edit.setObjectName("output_console")
        self.setStyleSheet("""
            QMainWindow { background-color: #f0f0f0; }
            QTabWidget::pane { border: 1px solid #ccc; background-color: #ffffff; }
            QTabBar::tab {
                background: #e0e0e0; border: 1px solid #c0c0c0;
                border-bottom: none; border-top-left-radius: 4px;
                border-top-right-radius: 4px; min-width: 150px;
                padding: 10px; font-weight: bold; color: #333;
            }
            QTabBar::tab:selected { background: #ffffff; color: #000; }
            QTabBar::tab:hover { background: #d0d0d0; }
            QGroupBox {
                border: 1px solid #ccc; border-radius: 5px; margin-top: 1ex;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin; subcontrol-position: top center;
                padding: 0 5px; background-color: #f0f0f0;
            }
            QPushButton {
                background-color: #0078D7; color: white; border-radius: 5px;
                padding: 8px 15px; font-weight: bold; border: none;
            }
            QPushButton:hover { background-color: #005A9E; }
            QPushButton:pressed { background-color: #004578; }
            QPushButton:disabled { background-color: #cccccc; color: #666666; }
            QLineEdit, QTextEdit {
                border: 1px solid #ccc; border-radius: 3px; padding: 5px;
                background-color: #ffffff;
            }
            QTextEdit#output_console { background-color: #e8f0f7; color: #333333; }
            QProgressBar {
                border: 1px solid #ccc; border-radius: 5px; text-align: center;
                background-color: #e0e0e0;
            }
            QProgressBar::chunk { background-color: #0078D7; border-radius: 4px; }
        """)

    @pyqtSlot(int) # Decorator to mark this as a slot expecting an integer argument
    def switch_to_tab(self, index):
        """
        Slot to switch the current tab in the QTabWidget.
        """
        if index < self.notebook.count(): # Ensure the index is valid
            self.notebook.setCurrentIndex(index)
        else:
            print(f"Attempted to switch to invalid tab index: {index}")

    def closeEvent(self, event):
        """
        This method is called when the main window is about to close.
        It ensures all background threads are stopped gracefully.
        """
        print("Closing application. Stopping all background threads...")
        for i in range(self.notebook.count()):
            tab = self.notebook.widget(i)
            # Check if the tab has a 'reset_process' method (our threaded tabs do)
            if hasattr(tab, 'reset_process'):
                tab.reset_process()
        
        event.accept() # Proceed with closing the window

if __name__ == "__main__":
    # Fix 1: Set High DPI scaling attribute BEFORE QApplication is created
    # This ensures that GUI elements scale correctly on high-resolution screens.
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app = QApplication(sys.argv)
    # A modern style is recommended for better cross-platform look and feel
    app.setStyle("Fusion") 
    main_window = MainWindow()
    main_window.show()
    main_window.open_welcome_window()
    sys.exit(app.exec_())