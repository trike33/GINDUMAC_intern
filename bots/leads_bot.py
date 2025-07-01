import sys
import pyautogui
import platform
import time
# NEW: Import QInputDialog for the selection dialog
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QInputDialog
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

        self.current_step = 0
        self.command_key = "command" if platform.system() == "Darwin" else "ctrl"
        self.steps = self.define_steps()
        self.init_ui()
        self.update_display()

    def apply_dark_mode_stylesheet(self):
        """Applies a simple dark theme to the widget."""
        self.setStyleSheet(DARK_STYLESHEET)
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
            {"title": "1. Abrir lead nuevo", "desc": "Focus Left & Click at (278, 292)", "func": self.action_focus_left_and_click_1},
            {"title": "2. Expandir, copiar y procesar el ULTIMO mail", "desc": "Lo ultimo de la conversacion debe ser el mail a procesar! Incluye delays de 3s", "func": self.execute_main_sequence},
            {"title": "3. 3 puntos, reply y pegamos la respuesta", "desc": "Focus Left, Double Click, then Click & Paste (incluye delays de 3s)", "func": self.action_focus_left_and_perform_sequence},
            {"title": "4. Le damos a send y cambiamos el status a i-email-sent", "desc": "Click, wait 3s, then click twice more", "func": self.combined_click_action},
            {"title": "5. Volvemos a la pagina principal de los leads", "desc": "Click at (155, 171)", "func": lambda: pyautogui.click(*self.scale_coords(155, 171), duration=1)},
            {"title": "6. Scroll Down to next lead", "desc": "Simulate scrolling down via mouse drag", "func": self.action_simulated_scroll},
        ]
        return steps

    def init_ui(self):
        self.setWindowTitle('Leads Bot (Dynamic & Endless)')
        self.setGeometry(300, 300, 500, 500)
        
        layout = QVBoxLayout()
        
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        layout.addWidget(self.text_display)
        
        button_layout = QHBoxLayout()
        
        prev_button = QPushButton('Previous (Left Arrow)')
        prev_button.clicked.connect(self.prev_step)
        
        next_button = QPushButton('Next (Right Arrow)')
        next_button.clicked.connect(self.next_step)

        # MODIFIED: Changed button text and connected it to the new jump_to_step method
        jump_button = QPushButton('Jump to Step...')
        jump_button.clicked.connect(self.jump_to_step)
        
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
        is_dark = "dark" in self.styleSheet() 
        highlight_color = "#00C7B1" if is_dark else "green"

        content = "<h1>Automation Steps (Looping)</h1>"
        for i, step in enumerate(self.steps):
            # NEW: Get the title from the step dictionary
            title = step.get('title', f"Step {i+1}") # Fallback if title is missing
            if i == self.current_step:
                # MODIFIED: Added the title to the display string
                content += f"<p><b><font color='{highlight_color}'>➡️ {title}:</font></b><br>&nbsp;&nbsp;&nbsp;{step['desc']}</p>"
            else:
                # MODIFIED: Added the title to the display string
                content += f"<p><font color='gray'>&nbsp;&nbsp;&nbsp;<b>{title}:</b><br>&nbsp;&nbsp;&nbsp;{step['desc']}</font></p>"
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

    # MODIFIED: Replaced jump_to_paste with jump_to_step
    def jump_to_step(self):
        """
        Opens a dialog to allow the user to select an arbitrary step to jump to.
        """
        if not self.steps:
            return

        # 1. Create a list of step descriptions for the user to choose from.
        step_descriptions = [step['title'] for step in self.steps]
        
        # 2. Show the input dialog with the list of steps.
        item, ok = QInputDialog.getItem(self, "Jump to Step", 
                                        "Select a step to jump to:", step_descriptions, self.current_step, False)
        
        # 3. If the user clicked "OK" and selected an item, find its index and update the current step.
        if ok and item:
            # Find the index of the selected description
            try:
                new_index = step_descriptions.index(item)
                self.current_step = new_index
                self.update_display()
                print(f"Jumped to step {self.current_step}: {self.steps[self.current_step]['title']}")
            except ValueError:
                # This should not happen if the item comes from the list, but it's good practice
                print(f"Error: Could not find step '{item}'.")

            
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

    def combined_click_action(self):
        """Clicks at three locations with a delay in the middle."""
        print("Executing combined click action.")
        # First click from the old step 4
        pyautogui.click(*self.scale_coords(921, 1063), duration=1)
        
        # Add the 3-second delay
        print("Waiting for 3 seconds...")
        time.sleep(3)
        
        # Clicks from the old step 5
        pyautogui.click(*self.scale_coords(207, 344), duration=1)
        pyautogui.click(*self.scale_coords(207, 414), duration=1)

    def action_simulated_scroll(self):
        """Moves the mouse to a start position and drags to an end position to simulate a scroll."""
        print("Simulating scroll down.")
        
        # Get scaled coordinates for start and end positions
        start_x, start_y = self.scale_coords(992, 412)
        end_x, end_y = self.scale_coords(992, 441)
        
        # Move to the start position
        pyautogui.moveTo(start_x, start_y, duration=0.5)
        
        # Drag to the end position to simulate the scroll
        pyautogui.dragTo(end_x, end_y, duration=1, button='left')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = AutomationStepper()
    if '--dark' in sys.argv:
        ex.apply_dark_mode_stylesheet()
    ex.show()
    sys.exit(app.exec_())