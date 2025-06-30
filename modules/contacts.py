# In modules/contacts.py (New Simplified Version)

import os
import pyperclip
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel, QPushButton,
                             QTextEdit, QGroupBox, QLineEdit, QProgressBar,
                             QMessageBox, QFileDialog, QHBoxLayout)
from PyQt5.QtCore import pyqtSignal
# email_logic is still needed, but Worker and QThread are not
from .email_logic import get_seller_followup_email_generator

class SellerFollowupTab(QWidget):
    output_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.email_generator_obj = None
        # No more thread or worker attributes
        self.init_ui()

    def init_ui(self):
        # This method remains the same as before
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
        main_layout.addWidget(self.progress_label)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.current_info_label)
        main_layout.addWidget(self.email_display_text)

        self.reset_process()

    def browse_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select CSV", "", "*.csv")
        if file_path:
            self.csv_path_qle.setText(file_path)

    def initialize_process(self):
        """
        Simplified process that runs directly on the main thread.
        This will cause a brief GUI freeze on large files, but prevents crashing.
        """
        csv_path = self.csv_path_qle.text()
        if not os.path.exists(csv_path):
            QMessageBox.warning(self, "Input Error", "Please select a valid CSV file.")
            return

        self.initialize_button.setEnabled(False)
        start_email = self.start_email_qle.text().strip()

        try:
            # Call the generator function directly, no thread
            self.email_generator_obj = get_seller_followup_email_generator(csv_path, start_email or None)

            # Update UI for success
            self.copy_next_button.setEnabled(True)
            self.reset_button.setEnabled(True)
            self.output_message.emit("[Contacts] Initialized successfully.\n")
            self.current_info_label.setText("Ready. Click 'Copy Next Email'.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during initialization: {e}")
            self.reset_process()


    def copy_next_email(self):
        if not self.email_generator_obj: return
        try:
            data = next(self.email_generator_obj)
            pyperclip.copy(data["message"])
            self.email_display_text.setText(data["message"])
            info = f"Row {data.get('row_index', 'N/A')} | Email: {data['email']}"
            self.current_info_label.setText(f"Current: {info}")
            self.update_progress(data['progress_current'], data['progress_total'])
            self.output_message.emit(f"[Contacts] Copied email for {data['email']}.\n")
        except StopIteration:
            QMessageBox.information(self, "Complete", "All emails processed.")
            self.reset_process()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process: {e}")
            self.reset_process()

    def reset_process(self):
        """Simplified reset with no thread management."""
        self.email_generator_obj = None

        self.initialize_button.setEnabled(True)
        self.copy_next_button.setEnabled(False)
        self.reset_button.setEnabled(False)
        self.email_display_text.clear()
        self.current_info_label.setText("Process reset. Select inputs to initialize.")
        self.update_progress(0, 0)

        if self.isVisible():
            self.output_message.emit("[Contacts] Process reset.\n")

    def update_progress(self, current, total):
        if total > 0:
            percent = int((current / total) * 100)
            self.progress_bar.setValue(percent)
            self.progress_label.setText(f"Progress: {current}/{total} ({percent}%)")
        else:
            self.progress_bar.setValue(0)
            self.progress_label.setText("Progress: 0/0 (0%)")
