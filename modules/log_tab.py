# log_tab.py
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QCheckBox,
    QLineEdit, QScrollArea, QMessageBox, QInputDialog
)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QFont
from cryptography.fernet import Fernet, InvalidToken
from hashlib import pbkdf2_hmac
import base64

class LogEntryWidget(QWidget):
    """
    A widget representing a single log entry, which is theme-aware and can
    update its appearance when the application theme changes.
    """
    def __init__(self, timestamp, message, encrypted, key_callback, is_dark=False):
        super().__init__()
        self.timestamp = timestamp
        self.encrypted = encrypted
        self.key_callback = key_callback
        self.is_dark = is_dark
        self.encrypted_message = message if encrypted else None
        self.plain_message = message if not encrypted else None

        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()
        self.setLayout(layout)

        self.label = QLabel()
        
        # Use QPalette to ensure text is visible in any theme by default
        palette = self.label.palette()
        palette.setColor(self.label.foregroundRole(), Qt.black)
        self.label.setPalette(palette)
        
        # Set font and other properties
        font = QFont('Segoe UI', 13)
        self.label.setFont(font)
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.label.setWordWrap(True)
        layout.addWidget(self.label, stretch=1)

        # Apply initial theme-aware styles
        self._apply_styles()

        if self.encrypted:
            self.label.setText(f"{self.timestamp}: *************")
            self.decrypt_btn = QPushButton("Decrypt")
            self.decrypt_btn.setMaximumWidth(120)
            self.decrypt_btn.clicked.connect(self.decrypt_message)
            layout.addWidget(self.decrypt_btn)
        else:
            self.label.setText(f"{self.timestamp}: {self.plain_message}")

    def update_theme(self, is_dark):
        """Updates the widget's color based on the new theme."""
        self.is_dark = is_dark
        self._apply_styles()

    def _apply_styles(self):
        """Sets the stylesheet based on the current theme and encryption status."""
        if self.is_dark:
            # Dark mode colors
            bg_color = "#5c1a33" if self.encrypted else "#1a4f5c"
            btn_bg_color = "#e91e63"
            btn_hover_color = "#c2185b"
            text_color = "white"
        else:
            # Original light mode colors
            bg_color = "#ffecf1" if self.encrypted else "#e0f7fa"
            btn_bg_color = "#ff4081"
            btn_hover_color = "#f50057"
            text_color = "black"
            
        # Ensure text color is set correctly if it's not handled by the main stylesheet
        palette = self.label.palette()
        palette.setColor(self.label.foregroundRole(), Qt.black if not self.is_dark else Qt.white)
        self.label.setPalette(palette)

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border-radius: 10px;
                padding: 10px;
                margin-bottom: 10px;
            }}
            QPushButton {{
                background-color: {btn_bg_color};
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {btn_hover_color};
            }}
        """)

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
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.entries = []
        self.temp_file_path = os.path.join("other", "temporal_log.txt")
        
        # Ensure the 'other' directory exists
        os.makedirs(os.path.dirname(self.temp_file_path), exist_ok=True)

        self.init_ui()
        self.load_existing_logs()

        # Connect to the main window's theme changed signal to update existing widgets
        if self.main_window:
            self.main_window.theme_changed.connect(self.update_all_themes)

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.log_container = QWidget()
        self.log_container.setObjectName("logContainer")
        self.log_layout = QVBoxLayout(self.log_container)
        self.log_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.log_container)
        layout.addWidget(self.scroll_area)

        input_widgets_container = QWidget()
        input_layout = QVBoxLayout(input_widgets_container)
        self.msg_input = QTextEdit()
        self.msg_input.setPlaceholderText("Enter your log message here...")
        self.msg_input.setFixedHeight(80)
        input_layout.addWidget(self.msg_input)

        self.encrypt_checkbox = QCheckBox("Encrypt")
        input_layout.addWidget(self.encrypt_checkbox)
        
        self.pwd_input = QLineEdit()
        self.pwd_input.setPlaceholderText("Password (if encrypting)")
        self.pwd_input.setEchoMode(QLineEdit.Password)
        input_layout.addWidget(self.pwd_input)

        btn_layout = QHBoxLayout()
        self.log_btn = QPushButton("Log Message")
        self.log_btn.clicked.connect(self.add_log)
        btn_layout.addWidget(self.log_btn)

        self.delete_btn = QPushButton("Delete Temp Log File")
        self.delete_btn.clicked.connect(self.delete_temp_file)
        btn_layout.addWidget(self.delete_btn)
        
        input_layout.addLayout(btn_layout)
        layout.addWidget(input_widgets_container)

    @pyqtSlot(bool)
    def update_all_themes(self, is_dark):
        """Loops through all existing log entries and tells them to update their theme."""
        for entry_widget in self.entries:
            entry_widget.update_theme(is_dark)

    def derive_key(self, password):
        if not password:
            return None
        # Use a securely generated salt in a real application
        salt = b'gindumac_static_salt_' 
        key = pbkdf2_hmac('sha256', password.encode(), salt, 100000, dklen=32)
        return Fernet(base64.urlsafe_b64encode(key))

    def add_log(self):
        message = self.msg_input.toPlainText().strip()
        if not message:
            return
            
        encrypted = self.encrypt_checkbox.isChecked()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        is_dark = self.main_window.is_dark_mode if self.main_window else False

        if encrypted:
            password = self.pwd_input.text()
            if not password:
                QMessageBox.warning(self, "Password Required", "A password is required for encryption.")
                return
            fernet = self.derive_key(password)
            encrypted_message = fernet.encrypt(message.encode()).decode()
            entry_widget = LogEntryWidget(timestamp, encrypted_message, True, self.derive_key, is_dark)
            self.save_log(timestamp, encrypted_message, encrypted=True)
        else:
            entry_widget = LogEntryWidget(timestamp, message, False, None, is_dark)
            self.save_log(timestamp, message, encrypted=False)

        self.log_layout.addWidget(entry_widget)
        self.entries.append(entry_widget)
        self.msg_input.clear()
        self.pwd_input.clear()
        self.encrypt_checkbox.setChecked(False)

    def save_log(self, timestamp, message, encrypted=False):
        flag = "ENC" if encrypted else "PLAIN"
        line = f"{timestamp}|||{flag}|||{message}\n"
        try:
            with open(self.temp_file_path, 'a', encoding='utf-8') as f:
                f.write(line)
        except IOError as e:
            QMessageBox.critical(self, "Save Error", f"Could not write to log file:\n{e}")

    def load_existing_logs(self):
        if not os.path.exists(self.temp_file_path):
            return
        is_dark = self.main_window.is_dark_mode if self.main_window else False
        try:
            with open(self.temp_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    parts = line.split("|||", 2)
                    if len(parts) != 3:
                        continue # Skip malformed lines

                    timestamp, flag, message = parts
                    encrypted = flag == "ENC"
                    
                    widget = LogEntryWidget(timestamp, message, encrypted, self.derive_key, is_dark)
                    self.log_layout.addWidget(widget)
                    self.entries.append(widget)
        except IOError as e:
            QMessageBox.critical(self, "Load Error", f"Could not read from log file:\n{e}")
        except Exception as e:
            QMessageBox.critical(self, "Parsing Error", f"An error occurred while parsing the log file:\n{e}")

    def delete_temp_file(self):
        reply = QMessageBox.question(self, "Confirm Deletion", 
                                     "Are you sure you want to permanently delete the temporary log file?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if os.path.exists(self.temp_file_path):
                try:
                    os.remove(self.temp_file_path)
                    QMessageBox.information(self, "Deleted", "Temporary log file has been deleted.")
                    self.clear_log_widgets()
                except OSError as e:
                    QMessageBox.critical(self, "Error", f"Could not delete file:\n{e}")

    def clear_log_widgets(self):
        for i in reversed(range(self.log_layout.count())):
            widget_item = self.log_layout.itemAt(i)
            if widget_item:
                widget = widget_item.widget()
                if widget:
                    widget.setParent(None)
                    widget.deleteLater()
        self.entries.clear()