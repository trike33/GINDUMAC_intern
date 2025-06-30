import random
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QLabel, 
                             QPushButton, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPainter, QColor

class WelcomeWindow(QMainWindow):
    def __init__(self, main_window=None):
        super().__init__()
        self.setWindowTitle("Welcome to GINDUMAC")
        self.setGeometry(200, 150, 900, 600)
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)
        layout.setAlignment(Qt.AlignCenter)

        content_box = QWidget()
        content_box.setStyleSheet("background-color: rgba(255,255,255,0.85); border-radius: 12px;")
        content_layout = QVBoxLayout(content_box)
        content_layout.setAlignment(Qt.AlignCenter)
        
        title = QLabel("Welcome to Our GINDUMAC Intern Application!")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        subtitle = QLabel(
            "This app is designed to help you manage tasks efficiently.<br>"
            '<span style="color:#e67e22; font-weight:bold;">NOTE: Always review email contents before sending!</span>'
        )
        subtitle.setFont(QFont("Segoe UI", 14))
        subtitle.setTextFormat(Qt.RichText)
        
        self.start_button = QPushButton("Get Started")
        self.start_button.clicked.connect(self.on_get_started_clicked)
        
        content_layout.addWidget(title)
        content_layout.addWidget(subtitle)
        content_layout.addWidget(self.start_button)
        layout.addWidget(content_box)

    def on_get_started_clicked(self):
        self.close()
        if self.main_window:
            self.main_window.notebook.setCurrentIndex(0)
