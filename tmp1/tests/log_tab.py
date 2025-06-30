# log_tab.py
import os
import tempfile
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QCheckBox,
    QLineEdit, QScrollArea, QMessageBox, QInputDialog
)
from PyQt5.QtCore import Qt
from cryptography.fernet import Fernet, InvalidToken
from hashlib import pbkdf2_hmac
import base64


class LogEntryWidget(QWidget):
    def __init__(self, timestamp, message, encrypted, key_callback):
        super().__init__()
        self.timestamp = timestamp
        self.encrypted = encrypted
        self.key_callback = key_callback
        self.encrypted_message = message if encrypted else None
        self.plain_message = message if not encrypted else None

        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QWidget {
                border-radius: 10px;
                padding: 10px;
                margin-bottom: 10px;
                font-size: 13pt;
                font-family: 'Segoe UI', sans-serif;
            }
        """)
        bg_color = "#ffecf1" if self.encrypted else "#e0f7fa"
        self.setStyleSheet(self.styleSheet() + f"background-color: {bg_color};")

        layout = QHBoxLayout()
        self.setLayout(layout)

        self.label = QLabel()
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.label.setWordWrap(True)
        layout.addWidget(self.label, stretch=1)

        if self.encrypted:
            self.label.setText(f"{self.timestamp}: *************")
            self.decrypt_btn = QPushButton("Decrypt")
            self.decrypt_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ff4081;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #f50057;
                }
            """)
            self.decrypt_btn.setMaximumWidth(120)
            self.decrypt_btn.clicked.connect(self.decrypt_message)
            layout.addWidget(self.decrypt_btn)
        else:
            self.label.setText(f"{self.timestamp}: {self.plain_message}")

    def decrypt_message(self):
        pwd, ok = QInputDialog.getText(self, "Password", "Enter password to decrypt:", QLineEdit.Password)
        if not ok or not pwd:
            return
        fernet = self.key_callback(pwd)
        if not fernet:
            QMessageBox.warning(self, "Error", "Failed to derive key.")
            return
        try:
            decrypted = fernet.decrypt(self.encrypted_message.encode()).decode()
            self.label.setText(f"{self.timestamp}: {decrypted}")
            self.decrypt_btn.setDisabled(True)
        except InvalidToken:
            QMessageBox.warning(self, "Error", "Invalid password or corrupted data.")


class LogTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.entries = []

        # Create temp file path only once per session
        self.temp_file_path = "temporal_log.txt"
        self.temp_file = open(self.temp_file_path, 'a+', encoding='utf-8')

        self.init_ui()
        self.load_existing_logs()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Scrollable log display
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.log_container = QWidget()
        self.log_layout = QVBoxLayout(self.log_container)
        self.log_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.log_container)

        layout.addWidget(self.scroll_area)

        # Input widgets
        self.msg_input = QTextEdit()
        self.msg_input.setPlaceholderText("Enter your log message here...")
        self.msg_input.setFixedHeight(80)

        self.encrypt_checkbox = QCheckBox("Encrypt")
        self.pwd_input = QLineEdit()
        self.pwd_input.setPlaceholderText("Password (if encrypting)")
        self.pwd_input.setEchoMode(QLineEdit.Password)

        self.log_btn = QPushButton("Log Message")
        self.log_btn.clicked.connect(self.add_log)

        self.delete_btn = QPushButton("Delete Temp Log File")
        self.delete_btn.clicked.connect(self.delete_temp_file)

        input_layout = QVBoxLayout()
        input_layout.addWidget(self.msg_input)
        input_layout.addWidget(self.encrypt_checkbox)
        input_layout.addWidget(self.pwd_input)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.log_btn)
        btn_layout.addWidget(self.delete_btn)
        input_layout.addLayout(btn_layout)

        layout.addLayout(input_layout)

    def derive_key(self, password):
        if not password:
            return None
        key = pbkdf2_hmac('sha256', password.encode(), b'salt_', 100000, dklen=32)
        return Fernet(base64.urlsafe_b64encode(key))

    def add_log(self):
        message = self.msg_input.toPlainText().strip()
        if not message:
            return
        encrypted = self.encrypt_checkbox.isChecked()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if encrypted:
            password = self.pwd_input.text()
            fernet = self.derive_key(password)
            if not fernet:
                QMessageBox.warning(self, "Error", "Password required for encryption.")
                return
            encrypted_message = fernet.encrypt(message.encode()).decode()
            entry_widget = LogEntryWidget(timestamp, encrypted_message, True, self.derive_key)
            self.save_log(timestamp, encrypted_message, encrypted=True)
        else:
            entry_widget = LogEntryWidget(timestamp, message, False, None)
            self.save_log(timestamp, message, encrypted=False)

        self.log_layout.addWidget(entry_widget)
        self.entries.append(entry_widget)
        self.msg_input.clear()
        self.pwd_input.clear()

    def save_log(self, timestamp, message, encrypted=False):
        flag = "ENC" if encrypted else "PLAIN"
        line = f"{timestamp}|||{flag}|||{message}\n"
        with open(self.temp_file_path, 'a', encoding='utf-8') as f:
            f.write(line)

    def load_existing_logs(self):
        if not os.path.exists(self.temp_file_path):
            return
        with open(self.temp_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    timestamp, flag, message = line.strip().split("|||")
                    encrypted = flag == "ENC"
                    widget = LogEntryWidget(timestamp, message, encrypted, self.derive_key)
                    self.log_layout.addWidget(widget)
                    self.entries.append(widget)
                except ValueError:
                    continue  # Skip malformed lines

    def delete_temp_file(self):
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
            QMessageBox.information(self, "Deleted", "Temporary log file deleted.")
            self.clear_log_widgets()

    def clear_log_widgets(self):
        for i in reversed(range(self.log_layout.count())):
            widget = self.log_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.entries.clear()
