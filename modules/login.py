from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QMessageBox, QApplication, QSizePolicy, QSpacerItem
)
from PyQt5.QtCore import Qt, QTimer
import hashlib
import json
import os

CREDENTIALS_FILE = "other/credentials.json"

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GINDUMAC INTERN - Login")
        self.setFixedSize(550, 380) # Increased height slightly for the status label
        self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.MSWindowsFixedSizeDialogHint)
        
        # --- NEW: Login attempt counter ---
        self.login_attempts = 0
        self.MAX_ATTEMPTS = 5
        # --- END NEW ---
        
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                            stop:0 #003366, stop:1 #007acc);
                border-radius: 12px;
            }
            QLabel#title {
                color: white;
                font-size: 22px;
                font-weight: bold;
                margin-bottom: 18px;
                qproperty-alignment: AlignCenter;
                font-family: Helvetica, Arial, sans-serif;
            }
            QLabel {
                color: white;
                font-weight: 600;
                font-family: Helvetica, Arial, sans-serif;
                margin-bottom: 6px;
            }
            QLabel#status_label {
                color: #ffdddd;
                font-weight: bold;
                font-size: 13px;
                qproperty-alignment: AlignCenter;
            }
            QLineEdit {
                background-color: rgba(255,255,255,0.95);
                border: 2px solid white;
                border-radius: 10px;
                padding: 8px 12px;
                font-size: 14px;
                font-family: Helvetica, Arial, sans-serif;
                color: #222;
            }
            QLineEdit:focus {
                border: 2px solid #001f4d;
                background-color: #f0f8ff;
            }
            QPushButton#login_btn {
                background-color: #001f4d;
                color: white;
                font-weight: bold;
                border-radius: 12px;
                padding: 10px;
                font-size: 16px;
                font-family: Helvetica, Arial, sans-serif;
            }
            QPushButton#login_btn:hover {
                background-color: #0059b3;
            }
            QPushButton#login_btn:pressed {
                background-color: #003366;
            }
            QPushButton#login_btn:disabled {
                background-color: #555;
                color: #999;
            }
            QCheckBox {
                color: white;
                font-family: Helvetica, Arial, sans-serif;
                font-weight: 600;
                margin-top: 10px;
            }
            QPushButton#toggle_pwd {
                border: none;
                background: transparent;
                color: #001f4d;
                font-weight: bold;
                font-size: 14px;
                padding-left: 6px;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 25, 30, 20)
        main_layout.setSpacing(10)

        self.title_label = QLabel("GINDUMAC INTERN")
        self.title_label.setObjectName("title")
        main_layout.addWidget(self.title_label)

        main_layout.addWidget(QLabel("Username"))
        self.username_edit = QLineEdit()
        main_layout.addWidget(self.username_edit)

        main_layout.addWidget(QLabel("Password"))
        pwd_layout = QHBoxLayout()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        pwd_layout.addWidget(self.password_edit)

        self.toggle_pwd_btn = QPushButton("Show")
        self.toggle_pwd_btn.setObjectName("toggle_pwd")
        self.toggle_pwd_btn.setCheckable(True)
        self.toggle_pwd_btn.toggled.connect(self.toggle_password)
        pwd_layout.addWidget(self.toggle_pwd_btn)
        main_layout.addLayout(pwd_layout)

        self.remember_cb = QCheckBox("Remember Me")
        main_layout.addWidget(self.remember_cb)
        
        # --- NEW: Status label for feedback ---
        self.status_label = QLabel("")
        self.status_label.setObjectName("status_label")
        main_layout.addWidget(self.status_label)
        # --- END NEW ---
        
        main_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.login_btn = QPushButton("Login")
        self.login_btn.setObjectName("login_btn")
        self.login_btn.clicked.connect(self.try_login)
        main_layout.addWidget(self.login_btn)

        self.load_saved_credentials()
        self.login_btn.setDefault(True)

    def toggle_password(self, checked):
        if checked:
            self.password_edit.setEchoMode(QLineEdit.Normal)
            self.toggle_pwd_btn.setText("Hide")
        else:
            self.password_edit.setEchoMode(QLineEdit.Password)
            self.toggle_pwd_btn.setText("Show")

    def load_saved_credentials(self):
        if not os.path.exists(CREDENTIALS_FILE):
            return
        try:
            with open(CREDENTIALS_FILE, "r") as f:
                data = json.load(f)
            username = data.get("username", "")
            password = data.get("password_plain", "") # Using plain for saved pwd
            if username and password:
                self.username_edit.setText(username)
                self.password_edit.setText(password)
                self.remember_cb.setChecked(True)
        except Exception as e:
            print("Error loading saved credentials:", e)

    def save_credentials(self, username, password):
        data = {"username": username, "password_plain": password}
        with open(CREDENTIALS_FILE, "w") as f:
            json.dump(data, f)

    def clear_saved_credentials(self):
        if os.path.exists(CREDENTIALS_FILE):
            os.remove(CREDENTIALS_FILE)

    def try_login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text()

        correct_username = "joanf"
        correct_password_hash = "b78a99031c25adef84ee89e2e88137e4"
        entered_password_hash = hashlib.md5(password.encode()).hexdigest()

        if username == correct_username and entered_password_hash == correct_password_hash:
            self.status_label.setText("✅ Login successful!")
            self.status_label.setStyleSheet("color: #aaffaa;")
            if self.remember_cb.isChecked():
                self.save_credentials(username, password)
            else:
                self.clear_saved_credentials()
            
            # Accept after a short delay to show success message
            QTimer.singleShot(500, self.accept)
        else:
            # --- MODIFIED: Handle failed login attempts ---
            self.login_attempts += 1
            attempts_left = self.MAX_ATTEMPTS - self.login_attempts

            if attempts_left > 0:
                self.status_label.setText(f"Incorrect username or password. {attempts_left} attempts left.")
                QMessageBox.warning(self, "Login Failed", f"Incorrect username or password.\nYou have {attempts_left} attempts remaining.")
            else:
                self.status_label.setText("Maximum login attempts exceeded.")
                self.login_btn.setEnabled(False) # Disable login button
                QMessageBox.critical(self, "Login Locked", 
                                     "You have exceeded the maximum number of login attempts.\n"
                                     "Please restart the application.")
            # --- END MODIFIED ---
