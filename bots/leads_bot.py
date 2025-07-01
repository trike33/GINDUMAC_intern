import sys
import pyautogui
import platform
import time
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt

# A simple dark theme for when the bot is launched from a dark-themed parent
DARK_STYLESHEET = """
QWidget {
    background-color: #2E2E2E;
    color: #E0E0E0;
    font-family: sans-serif;
}
QTextEdit {
    background-color: #252525;
    border: 1px solid #555555;
    border-radius: 3px;
    padding: 5px;
}
QPushButton {
    background-color: #00C7B1;
    color: white;
    border-radius: 5px;
    padding: 8px 15px;
    font-weight: bold;
    border: none;
}
QPushButton:hover {
    background-color: #00A997;
}
QPushButton:pressed {
    background-color: #008B7D;
}
"""

class AutomationStepper(QWidget):
    def __init__(self):
        super().__init__()
        self.reference_width = 1920
        self.reference_height = 1080
        self.screen_width, self.screen_height = pyautogui.size()
        #print(f"CRITICAL INFORMATION: THIS SCRIPT MUST BE USED WITH A FIREFOX BROWSER AT 80% OF ZOOM + SPLIT VIEW")
        #print(f"Reference screen size: {self.reference_width}x{self.reference_height}")
        #print(f"Current screen size: {self.screen_width}x{self.screen_height}")

        self.current_step = 0
        self.command_key = "command" if platform.system() == "Darwin" else "ctrl"
        self.steps = self.define_steps()
        self.init_ui()
        self.update_display()

    def apply_dark_mode_stylesheet(self):
        """Applies a simple dark theme to the widget."""
        self.setStyleSheet(DARK_STYLESHEET)
        # Also update the display for dark mode text color
        self.update_display()

    def scale_coords(self, x, y):
        scaled_x = int((x / self.reference_width) * self.screen_width)
        scaled_y = int((y / self.reference_height) * self.screen_height)
        return scaled_x, scaled_y

    def scale_region(self, x, y, w, h):
        scaled_x, scaled_y = self.scale_coords(x, y)
        scaled_w = int((w / self.reference_width) * self.screen_width)
        scaled_h = int((h / self.reference_height) * self.screen_height)
        return scaled_x, scaled_y, scaled_w, scaled_h

    def define_steps(self):
        steps = [
            {"desc": "Focus Left & Click at (278, 292)", "func": self.action_focus_left_and_click_1},
            {"desc": "Execute Main Sequence (Click, Copy, Paste on Right)", "func": self.execute_main_sequence},
            {"desc": "Focus Left, Double Click, then Click & Paste", "func": self.action_focus_left_and_perform_sequence, "jump_target": True},
            {"desc": "Click at (921, 1063)", "func": lambda: pyautogui.click(*self.scale_coords(921, 1063), duration=1)},
            {"desc": "Click at (207, 344) & (207, 414)", "func": self.double_click_action_2},
            {"desc": "Click at (155, 171)", "func": lambda: pyautogui.click(*self.scale_coords(155, 171), duration=1)},
        ]
        return steps

    def init_ui(self):
        self.setWindowTitle('PyAutoGUI Stepper (Dynamic & Endless)')
        self.setGeometry(300, 300, 500, 500)
        
        layout = QVBoxLayout()
        
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        layout.addWidget(self.text_display)
        
        button_layout = QHBoxLayout()
        
        prev_button = QPushButton('⬅️ Previous (Left Arrow)')
        prev_button.clicked.connect(self.prev_step)
        
        next_button = QPushButton('Next ➡️ (Right Arrow)')
        next_button.clicked.connect(self.next_step)

        jump_button = QPushButton('🚀 Jump to Paste')
        jump_button.clicked.connect(self.jump_to_paste)
        
        button_layout.addWidget(prev_button)
        button_layout.addWidget(next_button)
        button_layout.addWidget(jump_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Right:
            self.next_step()
        elif event.key() == Qt.Key_Left:
            self.prev_step()
        else:
            super().keyPressEvent(event)

    def update_display(self):
        is_dark = "dark" in self.styleSheet() # A simple check to see if a dark theme is applied
        highlight_color = "#00C7B1" if is_dark else "green"

        content = "<h1>Automation Steps (Looping)</h1>"
        for i, step in enumerate(self.steps):
            if i == self.current_step:
                content += f"<p><b><font color='{highlight_color}'>➡️ {step['desc']}</font></b></p>"
            else:
                content += f"<p><font color='gray'>&nbsp;&nbsp;&nbsp;{step['desc']}</font></p>"
        self.text_display.setHtml(content)

    def next_step(self):
        if self.steps:
            self.hide()
            QApplication.processEvents()
            
            self.steps[self.current_step]['func']()
            
            self.current_step = (self.current_step + 1) % len(self.steps)
            
            self.show()
            self.activateWindow()
            self.setFocus()
            self.update_display()

    def prev_step(self):
        if self.steps:
            self.current_step = (self.current_step - 1 + len(self.steps)) % len(self.steps)
            self.update_display()

    def jump_to_paste(self):
        for i, step in enumerate(self.steps):
            if step.get("jump_target"):
                self.current_step = i
                self.update_display()
                print(f"Jumped to step {i}: {step['desc']}")
                return
            
    def action_focus_left_and_click_1(self):
        pyautogui.click(*self.scale_coords(869, 47), duration=0.5)
        print("Set focus to LEFT screen.")
        pyautogui.click(*self.scale_coords(278, 292), duration=1)

    def execute_main_sequence(self):
        pyautogui.click(*self.scale_coords(438, 446), duration=1)
        print("Clicked at (438, 446).")
        
        print("Waiting for 3 seconds...")
        time.sleep(3)
        
        region = self.scale_region(394, 569, 223, 375)
        print(f"Dynamically calculated region: {region}")
        pyautogui.moveTo(region[0], region[1], duration=0.5)
        pyautogui.dragTo(region[0] + region[2], region[1] + region[3], duration=1, button='left')
        pyautogui.hotkey(self.command_key, 'c')
        print("Selection copied.")

        x_coord = (self.reference_width / 2) + 100
        pyautogui.click(*self.scale_coords(x_coord, 100), duration=0.5)
        print("Set focus to RIGHT screen.")
        pyautogui.click(*self.scale_coords(1112, 266), duration=1)
        pyautogui.hotkey(self.command_key, 'v')
        print("Pasted content.")

    def action_focus_left_and_perform_sequence(self):
        pyautogui.click(*self.scale_coords(869, 47), duration=0.5)
        print("Set focus to LEFT screen.")
        pyautogui.click(*self.scale_coords(615, 408), duration=1)
        pyautogui.click(*self.scale_coords(615, 438), duration=1)
        
        print("Waiting for 3 seconds...")
        time.sleep(3)
        
        pyautogui.click(*self.scale_coords(663, 952), duration=1)
        pyautogui.hotkey(self.command_key, 'v')
        print("Clicked and pasted content again.")

    def double_click_action_2(self):
        pyautogui.click(*self.scale_coords(207, 344), duration=1)
        pyautogui.click(*self.scale_coords(207, 414), duration=1)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = AutomationStepper()
    if '--dark' in sys.argv:
        ex.apply_dark_mode_stylesheet()
    ex.show()
    sys.exit(app.exec_())