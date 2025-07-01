import sys
import os

# Import PyQt5 modules
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QFrame, QGroupBox, QTabWidget,
    QDialog, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal
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
    # Signal to notify other widgets when the theme has changed.
    theme_changed = pyqtSignal(bool)

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

        # List of tabs that need a reference to the main window
        tabs_needing_main_window = ["Instructions", "Temporal Logs", "Leads Template"]

        for name, TabClass in tabs.items():
            # Pass main_window reference if the tab's name is in the list
            if name in tabs_needing_main_window:
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
        # 1. Define the color palettes
        if dark_mode:
            colors = {
                "bg_color": "#2E2E2E", "pane_bg": "#3C3C3C", "border_color": "#555555",
                "tab_bg": "#4A4A4A", "tab_selected_bg": "#3C3C3C", "text_color": "#E0E0E0",
                "text_color_selected": "#FFFFFF", "groupbox_bg": "#2E2E2E",
                "button_bg": "#00C7B1", "button_hover": "#00A997", "button_pressed": "#008B7D",
                "input_bg": "#3C3C3C", "console_bg": "#252525", "console_text": "#E0E0E0",
                "item_selected_bg": "#0078D7", "arrow_color": "dark"
            }
        else:
            colors = {
                "bg_color": "#f0f0f0", "pane_bg": "#ffffff", "border_color": "#ccc",
                "tab_bg": "#e0e0e0", "tab_selected_bg": "#ffffff", "text_color": "#003366",
                "text_color_selected": "#003366", "groupbox_bg": "#f0f0f0",
                "button_bg": "#0078D7", "button_hover": "#005A9E", "button_pressed": "#004578",
                "input_bg": "#ffffff", "console_bg": "#e8f0f7", "console_text": "#003366",
                "item_selected_bg": "#0078D7", "arrow_color": "light"
            }

        self.theme_button.setText("Light Mode" if dark_mode else "Dark Mode")
        
        # 2. Read the stylesheet template from the file
        try:
            with open("resources/stylesheet.qss", "r") as f:
                stylesheet_template = f.read()
        except FileNotFoundError:
            print("Error: stylesheet.qss not found. Make sure it's in the same directory as main_gui.py.")
            return
            
        # 3. Fill in the placeholders with the chosen colors and apply it
        final_stylesheet = stylesheet_template.format(**colors)
        self.setStyleSheet(final_stylesheet)


    def toggle_dark_mode(self):
        self.is_dark_mode = not self.is_dark_mode
        self.apply_stylesheet(self.is_dark_mode)
        # Emit the signal to notify all listening widgets of the theme change
        self.theme_changed.emit(self.is_dark_mode)

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