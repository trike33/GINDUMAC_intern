import sys
import os

# Import PyQt5 modules
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QFrame, QGroupBox, QTabWidget,
    QDialog, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QFont

# Ensure pyperclip is installed
try:
    import pyperclip
except ImportError:
    print("Error: pyperclip not found. Please install it using 'pip install pyperclip'")
    sys.exit(1)

# Import classes from your new modules
from modules.login import LoginDialog
from modules.log_tab import LogTab
from modules.stats import StatisticsTab
from modules.actions import ActionsTab
from modules.html_parser import HtmlToTextTab
from modules.leads import LeadsTab
from modules.email_sent import EmailSentTab
from modules.contacts import SellerFollowupTab
from modules.metabase import EmailGeneratorTab
from modules.welcome import WelcomeWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Integrated Email Tools")
        self.setGeometry(100, 100, 900, 800)
        self.is_dark_mode = False
        self.init_ui()
        self.apply_stylesheet(self.is_dark_mode)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Header with logo and buttons
        logo_frame = QFrame()
        logo_frame.setStyleSheet("background-color: #003366;") # Header color constant
        logo_layout = QHBoxLayout(logo_frame)
        logo_layout.setContentsMargins(10, 5, 10, 5)

        gindumac_label = QLabel("GINDUMAC GMBH ®")
        gindumac_label.setFont(QFont("Helvetica", 24, QFont.Bold))
        gindumac_label.setStyleSheet("color: white; padding: 10px; background-color: transparent;")
        
        logo_spacer = QWidget()
        logo_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        self.theme_button = QPushButton() # Text set by apply_stylesheet
        self.theme_button.setFixedSize(130, 35)
        self.theme_button.clicked.connect(self.toggle_dark_mode)

        welcome_button = QPushButton("🏠 Welcome")
        welcome_button.setFixedSize(130, 35)
        welcome_button.clicked.connect(self.open_welcome_window)

        logo_layout.addWidget(gindumac_label)
        logo_layout.addWidget(logo_spacer)
        logo_layout.addWidget(self.theme_button)
        logo_layout.addWidget(welcome_button)
        main_layout.addWidget(logo_frame)

        # Tabs
        self.notebook = QTabWidget()
        main_layout.addWidget(self.notebook)
        
        # Tab definitions using imported classes
        tabs = {
            "Leads Template": LeadsTab,
            "Leads Follow-up": EmailSentTab,
            "Contacts": SellerFollowupTab,
            "Metabase": EmailGeneratorTab,
            "Temporal Logs": LogTab,
            "Statistics": StatisticsTab,
            "Instructions": ActionsTab,
            "HTML2Text": HtmlToTextTab
        }
        for name, TabClass in tabs.items():
            # Pass main_window reference if the tab needs it (e.g., ActionsTab)
            if name == "Instructions":
                tab = TabClass(self.notebook, main_window=self)
            else:
                tab = TabClass(self.notebook)

            if hasattr(tab, 'output_message'):
                tab.output_message.connect(self.insert_output)
            self.notebook.addTab(tab, name)

        # Output Console
        output_group_box = QGroupBox("Application Output")
        output_layout = QVBoxLayout(output_group_box)
        self.output_text_edit = QTextEdit()
        self.output_text_edit.setObjectName("output_console")
        self.output_text_edit.setReadOnly(True)
        self.output_text_edit.setFont(QFont("Courier", 10))
        output_layout.addWidget(self.output_text_edit)
        main_layout.addWidget(output_group_box)
        main_layout.setStretchFactor(self.notebook, 3)
        main_layout.setStretchFactor(output_group_box, 1)

        self.insert_output("Welcome to the Integrated Email Tools!\n" + "="*70 + "\n")

    def apply_stylesheet(self, dark_mode=False):
        if dark_mode:
            bg_color, pane_bg, border_color = "#2E2E2E", "#3C3C3C", "#555555"
            tab_bg, tab_selected_bg = "#4A4A4A", "#3C3C3C"
            text_color, text_color_selected = "#E0E0E0", "#FFFFFF"
            groupbox_bg = "#2E2E2E"
            button_bg, button_hover, button_pressed = "#00C7B1", "#00A997", "#008B7D"
            input_bg, console_bg, console_text = "#3C3C3C", "#252525", "#E0E0E0"
        else:
            bg_color, pane_bg, border_color = "#f0f0f0", "#ffffff", "#ccc"
            tab_bg, tab_selected_bg = "#e0e0e0", "#ffffff"
            text_color, text_color_selected = "#003366", "#003366"
            groupbox_bg = "#f0f0f0"
            button_bg, button_hover, button_pressed = "#0078D7", "#005A9E", "#004578"
            input_bg, console_bg, console_text = "#ffffff", "#e8f0f7", "#003366"

        self.theme_button.setText("Light Mode" if dark_mode else "Dark Mode")
        
        self.setStyleSheet(f"""
            QMainWindow, QDialog {{ background-color: {bg_color}; }}
            QLabel, QCheckBox {{ color: {text_color}; }}
            QTabWidget::pane {{ border: 1px solid {border_color}; background-color: {pane_bg}; }}
            QTabBar::tab {{
                background: {tab_bg}; border: 1px solid {border_color};
                border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px;
                min-width: 120px; padding: 10px; font-weight: bold; color: {text_color};
            }}
            QTabBar::tab:selected {{ background: {tab_selected_bg}; color: {text_color_selected}; }}
            QGroupBox {{
                border: 1px solid {border_color}; border-radius: 5px; margin-top: 1ex;
                font-weight: bold; color: {text_color};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin; subcontrol-position: top center;
                padding: 0 5px; background-color: {groupbox_bg}; color: {button_bg};
            }}
            QPushButton {{
                background-color: {button_bg}; color: white; border-radius: 5px;
                padding: 8px 15px; font-weight: bold; border: none;
            }}
            QPushButton:hover {{ background-color: {button_hover}; }}
            QPushButton:pressed {{ background-color: {button_pressed}; }}
            QPushButton:disabled {{ background-color: #555; color: #999; }}
            QLineEdit, QTextEdit {{
                border: 1px solid {border_color}; border-radius: 3px; padding: 5px;
                background-color: {input_bg}; color: {text_color};
            }}
            QTextEdit#output_console {{ background-color: {console_bg}; color: {console_text}; }}
            QProgressBar {{
                border: 1px solid {border_color}; border-radius: 5px; text-align: center;
                background-color: {pane_bg}; color: {text_color};
            }}
            QProgressBar::chunk {{ background-color: {button_bg}; border-radius: 4px; }}
        """)


    def toggle_dark_mode(self):
        self.is_dark_mode = not self.is_dark_mode
        self.apply_stylesheet(self.is_dark_mode)

    def open_welcome_window(self):
        if not hasattr(self, 'welcome_win') or not self.welcome_win.isVisible():
            self.welcome_win = WelcomeWindow(main_window=self)
            self.welcome_win.show()
        self.welcome_win.raise_()
        self.welcome_win.activateWindow()

    @pyqtSlot(str)
    def insert_output(self, message):
        self.output_text_edit.moveCursor(self.output_text_edit.textCursor().End)
        self.output_text_edit.insertPlainText(message)
        self.output_text_edit.ensureCursorVisible()

    @pyqtSlot(int) 
    def switch_to_tab(self, index):
        if 0 <= index < self.notebook.count():
            self.notebook.setCurrentIndex(index)

    def closeEvent(self, event):
        """Ensure background threads are stopped gracefully on close."""
        print("Closing application. Resetting all tab processes...")
        for i in range(self.notebook.count()):
            tab = self.notebook.widget(i)
            if hasattr(tab, 'reset_process'):
                # This call will now block until the thread is safely stopped
                tab.reset_process()
        
        print("All threads stopped. Exiting.")
        event.accept() # Allow the window to close

if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    login = LoginDialog()
    if login.exec_() == QDialog.Accepted:
        main_window = MainWindow()
        main_window.show()
        main_window.open_welcome_window()
        sys.exit(app.exec_())
    else:
        sys.exit(0)