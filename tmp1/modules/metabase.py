import os
import pyperclip
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel, QPushButton,
                             QTextEdit, QGroupBox, QLineEdit, QProgressBar,
                             QMessageBox, QFileDialog, QHBoxLayout)
# --- FIX: Added 'Qt' to the import list here ---
from PyQt5.QtCore import pyqtSignal, Qt
from .email_logic import get_lead_email_generator

class EmailGeneratorTab(QWidget):
    output_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.email_generator_obj = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        self.warning_label = QLabel("<span style='color: orange;'>Please remember to check the name and lang!</span>")
        # This line will now work because 'Qt' is imported
        self.warning_label.setTextFormat(Qt.RichText)
        self.warning_label.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(self.warning_label)

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
        self.email_display_text.setFont(self.font())
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
        csv_path = self.csv_path_qle.text()
        price = self.machine_price_qle.text()
        link = self.machine_link_qle.text()
        name = self.machine_name_qle.text()

        if not all([csv_path, price, link, name]) or not os.path.exists(csv_path):
            QMessageBox.warning(self, "Input Error", "Please fill all fields and select a valid CSV.")
            return

        self.initialize_button.setEnabled(False)
        self.output_message.emit("[Metabase] Initializing...\n")

        try:
            self.email_generator_obj = get_lead_email_generator(csv_path, price, link, name)

            self.copy_next_button.setEnabled(True)
            self.reset_button.setEnabled(True)
            self.output_message.emit(f"[Metabase] Initialized for '{self.machine_name_qle.text()}'.\n")
            self.current_info_label.setText("Ready. Click 'Copy Next Email'.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during initialization: {e}")
            self.reset_process()

    def copy_next_email(self):
        if not self.email_generator_obj:
            return
        try:
            data = next(self.email_generator_obj)
            pyperclip.copy(data["message"])
            self.email_display_text.setText(data["message"])
            info = f"Email: {data['email']} | Country: {data['country']}"
            self.current_info_label.setText(f"Current: {info}")
            self.update_progress(data['progress_current'], data['progress_total'])
            self.output_message.emit(f"[Metabase] Copied email for {data['email']}.\n")
        except StopIteration:
            QMessageBox.information(self, "Complete", "All eligible emails processed.")
            self.output_message.emit("[Metabase] Process complete.\n")
            self.reset_process()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process next email: {e}")
            self.reset_process()

    def reset_process(self):
        self.email_generator_obj = None

        self.initialize_button.setEnabled(True)
        self.copy_next_button.setEnabled(False)
        self.reset_button.setEnabled(False)
        self.email_display_text.clear()
        self.current_info_label.setText("Process reset. Select inputs to initialize.")
        self.update_progress(0, 0)
        
        if self.isVisible():
            self.output_message.emit("[Metabase] Process reset.\n")

    def update_progress(self, current, total):
        if total > 0:
            percent = int((current / total) * 100)
            self.progress_bar.setValue(percent)
            self.progress_label.setText(f"Progress: {current}/{total} ({percent}%)")
        else:
            self.progress_bar.setValue(0)
            self.progress_label.setText("Progress: 0/0 (0%)")
