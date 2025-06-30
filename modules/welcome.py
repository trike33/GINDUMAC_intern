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
            "We're excited to have you here.<br>"
            "This app is designed to help you manage tasks efficiently and collaborate seamlessly.<br>"
            "Explore its features and streamline your workflow.<br><br>"
            '<span style="color:#e67e22; font-weight:bold;">⚠️ NOTE: Always make sure to review the email contents before sending!</span> '
        )
        subtitle.setFont(QFont("Segoe UI", 14))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #34495e;")
        subtitle.setTextFormat(Qt.RichText)  # Enable HTML rendering in QLabel

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
