import os
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel, QPushButton,
                             QTextEdit, QGroupBox, QMessageBox)
from PyQt5.QtCore import pyqtSignal
import pyperclip

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
        self.URLS_FILE = "other/urls.txt"
        self.init_ui()
        self.load_url_preview()
        self.update_counters()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        btn_frame = QGroupBox("Select Language to Copy Template")
        btn_layout = QGridLayout(btn_frame)
        
        lang_data = [("🇬🇧 English", "English"), ("🇮🇹 Italian", "Italian"), ("🇫🇷 French", "French")]
        self.count_labels = {}
        for i, (text, lang) in enumerate(lang_data):
            button = QPushButton(text)
            button.clicked.connect(lambda _, l=lang: self.copy_template(l))
            self.count_labels[lang] = QLabel(f"{lang} clicks: 0")
            btn_layout.addWidget(button, i, 0)
            btn_layout.addWidget(self.count_labels[lang], i, 1)

        main_layout.addWidget(btn_frame)
        self.total_count_lbl = QLabel("Total clicks: 0")
        main_layout.addWidget(self.total_count_lbl)
        self.status_label = QLabel("Click a button to copy the template.")
        main_layout.addWidget(self.status_label)

        url_group = QGroupBox("URL Management")
        url_layout = QVBoxLayout(url_group)
        self.url_textbox = QTextEdit()
        save_urls_button = QPushButton("Save URLs to File")
        save_urls_button.clicked.connect(self.save_urls)
        self.url_preview_text = QTextEdit()
        self.url_preview_text.setReadOnly(True)
        url_layout.addWidget(QLabel("Enter URLs (one per line):"))
        url_layout.addWidget(self.url_textbox)
        url_layout.addWidget(save_urls_button)
        url_layout.addWidget(QLabel("Saved URLs Preview:"))
        url_layout.addWidget(self.url_preview_text)
        main_layout.addWidget(url_group)

    def copy_template(self, lang):
        pyperclip.copy(self.templates[lang])
        self.click_counts[lang] += 1
        self.status_label.setText(f"✅ {lang} template copied!")
        self.update_counters()
        self.output_message.emit(f"[Email Sent Tab] Copied {lang} template.\n")

    def update_counters(self):
        for lang, label in self.count_labels.items():
            label.setText(f"{lang} clicks: {self.click_counts[lang]}")
        self.total_count_lbl.setText(f"Total clicks: {sum(self.click_counts.values())}")

    def save_urls(self):
        content = self.url_textbox.toPlainText().strip()
        if not content: return
        try:
            with open(self.URLS_FILE, "a", encoding="utf-8") as f:
                if not self.timestamp_written:
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"\n\n--- Session started at {now} ---\n")
                    self.timestamp_written = True
                f.write(content + "\n")
            self.url_textbox.clear()
            self.load_url_preview()
            self.output_message.emit(f"[Email Sent Tab] URLs saved to {self.URLS_FILE}\n")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save URLs:\n{e}")

    def load_url_preview(self):
        try:
            if os.path.exists(self.URLS_FILE):
                with open(self.URLS_FILE, "r", encoding="utf-8") as f:
                    self.url_preview_text.setText(f.read().strip())
            else:
                self.url_preview_text.setText("(No URLs saved yet)")
        except Exception as e:
            self.url_preview_text.setText(f"(Error reading file: {e})")
