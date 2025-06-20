import sys
import tempfile
import os
import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QTextEdit, QCheckBox, QScrollArea, QMessageBox, QInputDialog, QSizePolicy
)
from PyQt5.QtCore import Qt
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet, InvalidToken
import base64
import json


def derive_fernet_key(password: str) -> Fernet:
    password_bytes = password.encode()
    salt = b"fixed_salt_12345"  # In production use a secure random salt per user
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
    return Fernet(key)


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

        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.label = QLabel()
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.label.setWordWrap(True)
        self.layout.addWidget(self.label, stretch=1)

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
            self.decrypt_btn.setMaximumWidth(90)
            self.decrypt_btn.clicked.connect(self.decrypt_message)
            self.layout.addWidget(self.decrypt_btn)
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



class LogApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Temporal Log Writer")

        self.temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w+', encoding='utf-8')
        self.temp_file_path = self.temp_file.name

        self.logs = []  # list of dicts: timestamp, encrypted(bool), message(str)

        self.load_existing_logs()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Scroll area for logs
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        main_layout.addWidget(self.scroll_area, stretch=1)

        self.logs_container = QWidget()
        self.logs_layout = QVBoxLayout()
        self.logs_layout.setAlignment(Qt.AlignTop)
        self.logs_container.setLayout(self.logs_layout)
        self.scroll_area.setWidget(self.logs_container)

        # Add all loaded logs to the UI
        for log in self.logs:
            self.add_log_widget(log["timestamp"], log["message"], log["encrypted"], add_to_list=False)

        # Message input big text box
        self.msg_input = QTextEdit()
        self.msg_input.setPlaceholderText("Enter log message here")
        self.msg_input.setFixedHeight(100)
        main_layout.addWidget(self.msg_input)

        # Controls: encrypt checkbox, password input, log button
        controls_layout = QHBoxLayout()

        self.encrypt_checkbox = QCheckBox("Encrypt")
        self.encrypt_checkbox.stateChanged.connect(self.encrypt_checked)
        controls_layout.addWidget(self.encrypt_checkbox)

        self.pwd_input = QLineEdit()
        self.pwd_input.setPlaceholderText("Password (if encrypt)")
        self.pwd_input.setEchoMode(QLineEdit.Password)
        self.pwd_input.setDisabled(True)
        controls_layout.addWidget(self.pwd_input)

        self.log_btn = QPushButton("Log")
        self.log_btn.clicked.connect(self.log_message)
        controls_layout.addWidget(self.log_btn)

        main_layout.addLayout(controls_layout)

        # Delete temp file button
        self.delete_btn = QPushButton("Delete temp log file")
        self.delete_btn.clicked.connect(self.delete_temp_file)
        main_layout.addWidget(self.delete_btn)

        self.resize(700, 500)

        # Message input box
        self.msg_input.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 2px solid #d0d0d0;
                border-radius: 10px;
                padding: 8px;
                font-size: 12pt;
            }
        """)

        self.pwd_input.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #ccc;
                border-radius: 6px;
                padding: 4px;
                font-size: 11pt;
            }
        """)

        self.log_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                padding: 8px 14px;
                border-radius: 6px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 8px 14px;
                border-radius: 6px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)

        self.encrypt_checkbox.setStyleSheet("font-size: 11pt;")

    def encrypt_checked(self, state):
        self.pwd_input.setEnabled(state == Qt.Checked)

    def add_log_widget(self, timestamp, message, encrypted, add_to_list=True):
        widget = LogEntryWidget(timestamp, message, encrypted, self.derive_fernet)
        self.logs_layout.addWidget(widget)
        if add_to_list:
            self.logs.append({"timestamp": timestamp, "encrypted": encrypted, "message": message})
            # Save to temp file immediately
            self.save_log_to_tempfile(timestamp, message, encrypted)

    def log_message(self):
        msg = self.msg_input.toPlainText().strip()
        if not msg:
            QMessageBox.warning(self, "Input Error", "Log message cannot be empty.")
            return

        encrypted = self.encrypt_checkbox.isChecked()
        password = self.pwd_input.text() if encrypted else None

        if encrypted and not password:
            QMessageBox.warning(self, "Input Error", "Password cannot be empty if encryption is selected.")
            return

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if encrypted:
            fernet = self.derive_fernet(password)
            encrypted_msg = fernet.encrypt(msg.encode()).decode()
            self.add_log_widget(timestamp, encrypted_msg, True)
        else:
            self.add_log_widget(timestamp, msg, False)

        self.msg_input.clear()
        self.encrypt_checkbox.setChecked(False)
        self.pwd_input.clear()

    def derive_fernet(self, password):
        try:
            return derive_fernet_key(password)
        except Exception:
            return None

    def save_log_to_tempfile(self, timestamp, message, encrypted):
        log_line = json.dumps({"timestamp": timestamp, "encrypted": encrypted, "message": message})
        with open(self.temp_file_path, "a", encoding="utf-8") as f:
            f.write(log_line + "\n")

    def load_existing_logs(self):
        if os.path.exists(self.temp_file_path):
            try:
                with open(self.temp_file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            self.logs.append(data)
                        except Exception:
                            pass
            except Exception:
                pass

    def delete_temp_file(self):
        if os.path.exists(self.temp_file_path):
            try:
                os.remove(self.temp_file_path)
                QMessageBox.information(self, "Deleted", "Temporary log file deleted.")
                # Clear logs from UI and memory
                while self.logs_layout.count():
                    item = self.logs_layout.takeAt(0)
                    widget = item.widget()
                    if widget:
                        widget.deleteLater()
                self.logs.clear()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to delete temp file:\n{e}")
        else:
            QMessageBox.information(self, "Info", "No temp log file to delete.")

    def closeEvent(self, event):
        if os.path.exists(self.temp_file_path):
            reply = QMessageBox.question(self, 'Delete temp file?',
                                         "Do you want to delete the temporary log file before exiting?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                try:
                    os.remove(self.temp_file_path)
                except:
                    pass
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LogApp()
    window.show()
    sys.exit(app.exec_())
