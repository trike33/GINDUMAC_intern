import sys
import pyautogui
import platform
import time
# NEW: Import QInputDialog and QComboBox for the selection dialog and dropdown
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QInputDialog, QComboBox, QLabel
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
QComboBox {
    border: 1px solid #555555;
    border-radius: 3px;
    padding: 1px 18px 1px 3px;
    min-width: 6em;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 15px;
    border-left-width: 1px;
    border-left-color: #555555;
    border-left-style: solid;
    border-top-right-radius: 3px;
    border-bottom-right-radius: 3px;
}
QLabel {
    font-weight: bold;
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
        # State for the dropdowns
        self.automation_choice = 1
        self.main_action_choice = 1 # 1: email gen, 2: drop prospect, 3: copy url
        self.main_action_options = ["1. email gen", "2. drop prospect", "3. copy url"]

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
        # MODIFIED: The list of steps is now dynamically generated based on the main action choice
        if self.main_action_choice == 1: # 1. email gen (step-by-step)
            steps = [
                {"title": "1. Abrir lead nuevo", "desc": "Focus Left & Click at (278, 292)", "func": self.action_focus_left_and_click_1},
                {"title": f"2. Expandir, copiar y procesar (Opción {self.automation_choice})", "desc": "Depende de la seleccion. Incluye delays de 3s", "func": self.dispatch_step_2_email_gen},
                {"title": f"3. 3 puntos, reply y pegar (Opción {self.automation_choice})", "desc": "Depende de la seleccion. Incluye delays de 3s", "func": self.dispatch_step_3_email_gen},
                {"title": "4. Le damos a send y cambiamos el status a i-email-sent", "desc": "Click, wait 3s, then click twice more", "func": self.combined_click_action},
                {"title": "5. Volvemos a la pagina principal de los leads", "desc": "Click at (155, 171)", "func": self.action_go_to_main_page},
                {"title": "6. Scroll Down to next lead", "desc": "Simulate scrolling down via mouse drag(from y:412 to y:445)", "func": self.action_simulated_scroll},
            ]
        elif self.main_action_choice == 2: # 2. drop prospect (consolidated)
             steps = [
                {"title": "1. Abrir lead nuevo", "desc": "Focus Left & Click at (278, 292)", "func": self.action_focus_left_and_click_1},
                {"title": "2. Drop Prospect", "desc": "Click en x:207 y:344 y luego en x:207 y:448", "func": self.action_drop_prospect},
                {"title": "3. Volvemos a la pagina principal de los leads", "desc": "Click at (155, 171)", "func": self.action_go_to_main_page},
                {"title": "4. Scroll Down to next lead", "desc": "Simulate scrolling down via mouse drag(from y:412 to y:445)", "func": self.action_simulated_scroll},
            ]
        elif self.main_action_choice == 3: # 3. copy url (consolidated)
             steps = [
                {"title": "1. Abrir lead nuevo", "desc": "Focus Left & Click at (278, 292)", "func": self.action_focus_left_and_click_1},
                {"title": "2. Copy URL", "desc": "Click en x:528 y:93 y copia la URL", "func": self.action_copy_url},
                {"title": "3. Volvemos a la pagina principal de los leads", "desc": "Click at (155, 171)", "func": self.action_go_to_main_page},
                {"title": "4. Scroll Down to next lead", "desc": "Simulate scrolling down via mouse drag(from y:412 to y:445)", "func": self.action_simulated_scroll},
            ]
        return steps

    def init_ui(self):
        self.setWindowTitle('Leads Bot (Dynamic & Endless)')
        self.setGeometry(300, 300, 500, 600)
        
        layout = QVBoxLayout()

        choice_layout_1 = QHBoxLayout()
        choice_label_1 = QLabel("Tipo de Automatización (para Email Gen):")
        self.automation_dropdown = QComboBox()
        self.automation_dropdown.addItems(["1", "2"])
        self.automation_dropdown.currentIndexChanged.connect(self.automation_changed)
        choice_layout_1.addWidget(choice_label_1)
        choice_layout_1.addWidget(self.automation_dropdown)
        choice_layout_1.addStretch()
        layout.addLayout(choice_layout_1)

        choice_layout_2 = QHBoxLayout()
        choice_label_2 = QLabel("Acción Principal:")
        self.main_action_dropdown = QComboBox()
        self.main_action_dropdown.addItems(self.main_action_options)
        self.main_action_dropdown.currentIndexChanged.connect(self.main_action_changed)
        choice_layout_2.addWidget(choice_label_2)
        choice_layout_2.addWidget(self.main_action_dropdown)
        choice_layout_2.addStretch()
        layout.addLayout(choice_layout_2)

        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        layout.addWidget(self.text_display)
        
        button_layout = QHBoxLayout()
        
        prev_button = QPushButton('Previous (Left Arrow)')
        prev_button.clicked.connect(self.prev_step)
        
        next_button = QPushButton('Next (Right Arrow)')
        next_button.clicked.connect(self.next_step)

        jump_button = QPushButton('Jump to Step...')
        jump_button.clicked.connect(self.jump_to_step)
        
        button_layout.addWidget(prev_button)
        button_layout.addWidget(next_button)
        button_layout.addWidget(jump_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def automation_changed(self, index):
        self.automation_choice = index + 1
        self.steps = self.define_steps() # Redefine to update titles
        self.update_display()
        #print(f"Automation choice for 'email gen' changed to: {self.automation_choice}")

    def main_action_changed(self, index):
        self.main_action_choice = index + 1
        self.current_step = 0 # Reset step count
        self.steps = self.define_steps() # Redefine steps for the new workflow
        self.update_display()
        #print(f"Main action changed to: {self.main_action_options[index]}")

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

        content = "<h1>Flujo Principal Actual</h1>"
        for i, step in enumerate(self.steps):
            title = step.get('title', f"Step {i+1}")
            if i == self.current_step:
                content += f"<p><b><font color='{highlight_color}'>➡️ {title}:</font></b><br>&nbsp;&nbsp;&nbsp;{step['desc']}</p>"
            else:
                content += f"<p><font color='gray'>&nbsp;&nbsp;&nbsp;<b>{title}:</b><br>&nbsp;&nbsp;&nbsp;{step['desc']}</font></p>"
        self.text_display.setHtml(content)

    def next_step(self):
        if self.steps:
            self.hide()
            QApplication.processEvents()
            
            # Execute the function for the current step
            self.steps[self.current_step]['func']()
            
            # Move to the next step in the sequence
            self.current_step = (self.current_step + 1) % len(self.steps)
            
            self.show()
            self.activateWindow()
            self.setFocus()
            self.update_display()

    def prev_step(self):
        if self.steps:
            self.current_step = (self.current_step - 1 + len(self.steps)) % len(self.steps)
            self.update_display()

    def jump_to_step(self):
        if not self.steps:
            return
        step_descriptions = [step['title'] for step in self.steps]
        item, ok = QInputDialog.getItem(self, "Jump to Step", 
                                        "Select a step to jump to:", step_descriptions, self.current_step, False)
        if ok and item:
            try:
                new_index = step_descriptions.index(item)
                self.current_step = new_index
                self.update_display()
            except ValueError:
                print(f"Error: Could not find step '{item}'.")

    # --- Dispatcher Functions for "email gen" ---
    def dispatch_step_2_email_gen(self):
        if self.automation_choice == 1:
            #print("Executing Action 2")
            self.execute_main_sequence()
        else:
            #print("Executing Action 2.1")
            self.execute_main_sequence_alternative()

    def dispatch_step_3_email_gen(self):
        if self.automation_choice == 1:
            #print("Executing Action 3")
            self.action_focus_left_and_perform_sequence()
        else:
            #print("Executing Action 3.1")
            self.action_focus_left_and_perform_sequence_alternative()

    # --- Main Action Functions ---
            
    def action_focus_left_and_click_1(self):
        pyautogui.click(*self.scale_coords(869, 47), duration=0.5)
        pyautogui.click(*self.scale_coords(278, 292), duration=1)

    def action_drop_prospect(self):
        #print("--- Running 'drop prospect' action ---")
        pyautogui.click(*self.scale_coords(207, 344), duration=1)
        pyautogui.click(*self.scale_coords(207, 448), duration=1)
        #print("--- Finished 'drop prospect' action ---")

    def action_copy_url(self):
        #print("--- Running 'copy url' action ---")
        pyautogui.click(*self.scale_coords(528, 93), duration=1)
        pyautogui.hotkey(self.command_key, 'c')
        #print("URL Copied.")
        #print("--- Finished 'copy url' action ---")

    def action_go_to_main_page(self):
        pyautogui.click(*self.scale_coords(155, 171), duration=1)

    # --- "Email Gen" Specific Actions ---
    def execute_main_sequence(self):
        pyautogui.click(*self.scale_coords(438, 446), duration=1)
        time.sleep(3)
        region = self.scale_region(394, 569, 223, 375)
        pyautogui.moveTo(region[0], region[1], duration=0.5)
        pyautogui.dragTo(region[0] + region[2], region[1] + region[3], duration=1, button='left')
        pyautogui.hotkey(self.command_key, 'c')
        x_coord = (self.reference_width / 2) + 100
        pyautogui.click(*self.scale_coords(x_coord, 100), duration=0.5)
        pyautogui.click(*self.scale_coords(1112, 266), duration=1)
        pyautogui.hotkey(self.command_key, 'v')

    def execute_main_sequence_alternative(self):
        #print("--- Running Alternative Main Sequence (2.1) ---")
        pyautogui.click(*self.scale_coords(438, 590), duration=1)
        time.sleep(3)
        region = self.scale_region(399, 733, 204, 335)
        pyautogui.moveTo(region[0], region[1], duration=0.5)
        pyautogui.dragTo(region[0] + region[2], region[1] + region[3], duration=1, button='left')
        pyautogui.hotkey(self.command_key, 'c')
        x_coord = (self.reference_width / 2) + 150
        pyautogui.click(*self.scale_coords(x_coord, 100), duration=0.5)
        pyautogui.click(*self.scale_coords(1115, 270), duration=1)
        pyautogui.hotkey(self.command_key, 'v')
        #print("--- Finished Alternative Main Sequence (2.1) ---")

    def action_focus_left_and_perform_sequence(self):
        pyautogui.click(*self.scale_coords(869, 47), duration=0.5)
        pyautogui.click(*self.scale_coords(615, 408), duration=1)
        pyautogui.click(*self.scale_coords(615, 438), duration=1)
        time.sleep(3)
        pyautogui.click(*self.scale_coords(663, 952), duration=1)
        pyautogui.hotkey(self.command_key, 'v')

    def action_focus_left_and_perform_sequence_alternative(self):
        #print("--- Running Alternative Paste Sequence (3.1) ---")
        pyautogui.click(*self.scale_coords(869, 47), duration=0.5)
        pyautogui.click(*self.scale_coords(620, 579), duration=1)
        pyautogui.click(*self.scale_coords(620, 605), duration=1)
        time.sleep(3)
        pyautogui.click(*self.scale_coords(663, 952), duration=1)
        pyautogui.hotkey(self.command_key, 'v')
        #print("--- Finished Alternative Paste Sequence (3.1) ---")

    def combined_click_action(self):
        pyautogui.click(*self.scale_coords(921, 1063), duration=1)
        time.sleep(3)
        pyautogui.click(*self.scale_coords(207, 344), duration=1)
        pyautogui.click(*self.scale_coords(207, 414), duration=1)

    def action_simulated_scroll(self):
        start_x, start_y = self.scale_coords(992, 412)
        end_x, end_y = self.scale_coords(992, 445)
        pyautogui.moveTo(start_x, start_y, duration=0.5)
        pyautogui.dragTo(end_x, end_y, duration=1, button='left')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = AutomationStepper()
    if '--dark' in sys.argv:
        ex.apply_dark_mode_stylesheet()
    ex.show()
    sys.exit(app.exec_())
