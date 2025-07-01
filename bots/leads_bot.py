import sys
import pyautogui
import platform
import time
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt

class AutomationStepper(QWidget):
    def __init__(self):
        super().__init__()
        # --- Get screen size ONCE at startup ---
        self.reference_width = 1920
        self.reference_height = 1080
        self.screen_width, self.screen_height = pyautogui.size()
	print(f"CRITICAL INFORMATION: THIS SCRIPT MUST BE USED WITH A FIREFOX BROWSER AT 80% OF ZOOM + SPLIT VIEW")
        print(f"Reference screen size: {self.reference_width}x{self.reference_height}")
        print(f"Current screen size: {self.screen_width}x{self.screen_height}")

        self.current_step = 0
        self.command_key = "command" if platform.system() == "Darwin" else "ctrl"
        self.steps = self.define_steps()
        self.init_ui()
        self.update_display()

    def scale_coords(self, x, y):
        """Scales coordinates from the reference resolution to the current screen resolution."""
        scaled_x = int((x / self.reference_width) * self.screen_width)
        scaled_y = int((y / self.reference_height) * self.screen_height)
        return scaled_x, scaled_y

    def scale_region(self, x, y, w, h):
        """Scales a region from the reference resolution to the current screen resolution."""
        scaled_x, scaled_y = self.scale_coords(x, y)
        scaled_w = int((w / self.reference_width) * self.screen_width)
        scaled_h = int((h / self.reference_height) * self.screen_height)
        return scaled_x, scaled_y, scaled_w, scaled_h

    def define_steps(self):
        """Defines the sequence of automation tasks with scaled coordinates and automatic focus clicks."""
        
        steps = [
            # --- Start on LEFT screen with explicit focus ---
            {"desc": "Focus Left & Click at (278, 292)", "func": self.action_focus_left_and_click_1},
            
            # --- Combined sequence of actions ---
            {"desc": "Execute Main Sequence (Click, Copy, Paste on Right)", "func": self.execute_main_sequence},

            # --- FOCUS CHANGE to LEFT and subsequent actions ---
            {"desc": "Focus Left, Double Click, then Click & Paste", "func": self.action_focus_left_and_perform_sequence, "jump_target": True},
            {"desc": "Click at (921, 1063)", "func": lambda: pyautogui.click(*self.scale_coords(921, 1063), duration=1)},
            {"desc": "Click at (207, 344) & (207, 414)", "func": self.double_click_action_2},
            {"desc": "Click at (155, 171)", "func": lambda: pyautogui.click(*self.scale_coords(155, 171), duration=1)},
        ]
        
        return steps

    def init_ui(self):
        """Sets up the GUI components."""
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
        """Handles keyboard presses for arrow key navigation."""
        if event.key() == Qt.Key_Right:
            self.next_step()
        elif event.key() == Qt.Key_Left:
            self.prev_step()
        else:
            super().keyPressEvent(event)

    def update_display(self):
        """Updates the text display to show the current state of steps."""
        content = "<h1>Automation Steps (Looping)</h1>"
        for i, step in enumerate(self.steps):
            if i == self.current_step:
                content += f"<p><b><font color='blue'>➡️ {step['desc']}</font></b></p>"
            else:
                content += f"<p><font color='gray'>&nbsp;&nbsp;&nbsp;{step['desc']}</font></p>"
        self.text_display.setHtml(content)

    def next_step(self):
        """Executes the current step and advances, looping back to the start."""
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
        """Moves to the previous step without re-executing actions."""
        if self.steps:
            self.current_step = (self.current_step - 1 + len(self.steps)) % len(self.steps)
            self.update_display()

    def jump_to_paste(self):
        """Jumps the current step to the 'Paste content again' action."""
        for i, step in enumerate(self.steps):
            if step.get("jump_target"):
                self.current_step = i
                self.update_display()
                print(f"Jumped to step {i}: {step['desc']}")
                return
            
    # --- Custom Action Functions ---

    def action_focus_left_and_click_1(self):
        """Sets focus to the left and immediately clicks."""
        pyautogui.click(*self.scale_coords(869, 47), duration=0.5)
        print("Set focus to LEFT screen.")
        pyautogui.click(*self.scale_coords(278, 292), duration=1)

    def execute_main_sequence(self):
        """Performs the main sequence: click, delay, copy, focus right, click, paste."""
        # 1. Click on the left
        pyautogui.click(*self.scale_coords(438, 446), duration=1)
        print("Clicked at (438, 446).")
        
        # 2. Delay for 3 seconds
        print("Waiting for 3 seconds...")
        time.sleep(3)
        
        # 3. Select region and copy
        region = self.scale_region(394, 569, 223, 375)
        print(f"Dynamically calculated region: {region}")
        pyautogui.moveTo(region[0], region[1], duration=0.5)
        pyautogui.dragTo(region[0] + region[2], region[1] + region[3], duration=1, button='left')
        pyautogui.hotkey(self.command_key, 'c')
        print("Selection copied.")

        # 4. Focus right, click, and paste
        x_coord = (self.reference_width / 2) + 100
        pyautogui.click(*self.scale_coords(x_coord, 100), duration=0.5)
        print("Set focus to RIGHT screen.")
        pyautogui.click(*self.scale_coords(1112, 266), duration=1)
        pyautogui.hotkey(self.command_key, 'v')
        print("Pasted content.")

    def action_focus_left_and_perform_sequence(self):
        """Sets focus left, double-clicks, delays, then clicks and pastes."""
        # Action 1: Focus left and double click
        pyautogui.click(*self.scale_coords(869, 47), duration=0.5)
        print("Set focus to LEFT screen.")
        pyautogui.click(*self.scale_coords(615, 408), duration=1)
        pyautogui.click(*self.scale_coords(615, 438), duration=1)
        
        # Action 2: Delay for 3 seconds
        print("Waiting for 3 seconds...")
        time.sleep(3)
        
        # Action 3: Click and paste
        pyautogui.click(*self.scale_coords(663, 952), duration=1)
        pyautogui.hotkey(self.command_key, 'v')
        print("Clicked and pasted content again.")

    def double_click_action_2(self):
        pyautogui.click(*self.scale_coords(207, 344), duration=1)
        pyautogui.click(*self.scale_coords(207, 414), duration=1)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = AutomationStepper()
    ex.show()
    sys.exit(app.exec_())
