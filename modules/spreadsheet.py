import sys
import csv
import json
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QLabel, QLineEdit, QFormLayout, QMessageBox,
    QFileDialog, QTabWidget, QComboBox, QListWidget, QListWidgetItem, QCheckBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

# --- Prompt Text ---
# The prompt for generating CSV data is stored here as a constant.
PROMPT_TEXT = """Based on the provided PDF brochure, generate two distinct CSV outputs in two separate, single code blocks.

**IMPORTANT NOTE ON INFORMATION SOURCE:** The PDF brochure should be considered the primary source of information. If a PDF is not provided or information is missing from the PDF, you MUST search for the required information online to complete the task.

**1. Model Information CSV:**

First, create a CSV file that lists the machine models. The output must strictly follow the format: `model_base,tipus_clasificador,valor_clasificador`.

- Identify every unique machine model from the column headers in the "Technical data" tables within the PDF.
- The `model_base` should be the main series name (e.g., "CHIRON 12 Series").
- The `tipus_clasificador` for all these entries will be "Model".
- The `valor_clasificador` will be the full model name (e.g., "FZ 12K S", "DZ 12K W MAGNUM", etc.).

**2. Technical Specifications CSV:**

Second, create a more detailed CSV of the technical specifications. Your primary goal is to map the data from the PDF to the standardized parameter names and units listed below.

- For each machine model, begin with a title line in the format: `Datos [Full Model Name]`.
- You must only take from the PDF or otherwise from internet the provided technical specs.
- Following each title, list its technical specifications. Each specification must be on a new line and strictly follow the comma-separated format: `parameter_name,value,unit`.

**MANDATORY PARAMETER MAPPING:**

You MUST map the data from the PDF to one of the following `parameter_name` options, using its corresponding `unit`.

| Parameter Name            | Unit |
|---------------------------|------|
| Machine Weight            | kg   |
| Machine Length            | mm   |
| Machine Height            | mm   |
| Machine Depth             | mm   |
| X-axis travel             | mm   |
| Z-axis travel             | mm   |
| Y-axis travel             | mm   |
| A-axis Min                | º    |
| A-axis Max                | º    |
| B-axis Min                | º    |
| B-axis Max                | º    |
| C-axis                    | º    |
| Number of axis            | N/A  |
| Control Brand             | N/A  |
| Control Model             | N/A  |
| Spindle Speed             | RPM  |
| spindle power             | kW   |
| taper size                | N/A  |
| number of tools           | N/A  |
| Through-spindle coolant   | N/A  |
| counter spindle           | N/A  |
| max. bar diameter         | mm   |
| max. workpiece diameter   | mm   |
| max. workpiece height     | mm   |
| table width               | mm   |
| table length              | mm   |
| Table load                | kg   |
| min. wire diameter        | mm   |
| max. wire diameter        | mm   |
| max. tool weight          | kg   |
| driven tools              | N/A  |
| Positioning Accuracy      | µm   |

**Formatting Rules:**

- If the PDF provides a parameter that is not in the list above, **do not include it**.
- If a parameter from the list is not in the PDF for a specific model, **do not include that line**.
- When the source data combines multiple axes into one line (e.g., "Travel X/Y/Z axis" with a value of "550/320/360 mm"), you must split this into three separate lines in the output, one for each axis, using the correct parameter name (e.g., `X-axis travel,550,mm`).
- If the unit is listed as "N/A", leave the unit field blank in the CSV.
- Present the entire result as a single block of text, with a blank line separating the data for each model.

**3. Provided technical specs:**
"""

# Path to the JSON file storing tech specs
RESOURCES_DIR = "resources"
TECH_SPECS_FILE = os.path.join(RESOURCES_DIR, "tech_specs.json")

class DataExtractionTab(QWidget):
    """
    A QWidget that contains a tabbed interface for data extraction tools:
    1. Tech Spec Formatter
    2. Model Formatter
    3. Prompt Generator
    """
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.tech_specs_data = {} # To store loaded tech specs from JSON
        self.load_tech_specs() # Load tech specs when initializing
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        # Create the individual tabs
        self.tech_spec_tab = QWidget()
        self.model_tab = QWidget()
        self.prompt_tab = QWidget()

        tabs.addTab(self.tech_spec_tab, "Tech Spec Formatter")
        tabs.addTab(self.model_tab, "Model Formatter")
        tabs.addTab(self.prompt_tab, "Prompt Generator")

        # Populate each tab with its widgets and logic
        self.create_tech_spec_tab()
        self.create_model_tab()
        self.create_prompt_tab()

        layout.addWidget(tabs)
        self.setLayout(layout)

    def load_tech_specs(self):
        """
        Loads the technical specifications from the JSON file.
        """
        if not os.path.exists(RESOURCES_DIR):
            os.makedirs(RESOURCES_DIR) # Create resources directory if it doesn't exist

        if not os.path.exists(TECH_SPECS_FILE):
            # If the file doesn't exist, create it with initial data
            initial_data = {
                "MILLING": {
                    "VERTICAL MACHINE CENTER": [
                        "Number of axis", "X-axis Travel", "Z-axis Travel", "Y-axis Travel",
                        "table width", "table length", "B-axis Min", "B-axis Max", "C-axis",
                        "Machine Weight"
                    ],
                    "HORIZONTAL MACHINE CENTER": [
                        "Number of axis", "X-axis Travel", "Z-axis Travel", "Y-axis Travel",
                        "B-axis Min", "B-axis Max", "C-axis", "Machine Weight"
                    ]
                },
                "TURNING": {
                    "HORIZONTAL TURNING": [
                        "Number of axis", "X-axis Travel", "Z-axis Travel", "Control Brand",
                        "Counter Spindle", "Driven tools"
                    ]
                }
            }
            try:
                with open(TECH_SPECS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(initial_data, f, indent=4)
                self.tech_specs_data = initial_data
                QMessageBox.information(self, "Info", f"'{TECH_SPECS_FILE}' created with default data.")
            except Exception as e:
                QMessageBox.critical(self, "File Error", f"Could not create '{TECH_SPECS_FILE}':\n{e}")
            return

        try:
            with open(TECH_SPECS_FILE, 'r', encoding='utf-8') as f:
                self.tech_specs_data = json.load(f)
        except FileNotFoundError:
            QMessageBox.warning(self, "File Not Found", f"The tech specs file '{TECH_SPECS_FILE}' was not found.")
            self.tech_specs_data = {}
        except json.JSONDecodeError:
            QMessageBox.critical(self, "JSON Error", f"Error decoding JSON from '{TECH_SPECS_FILE}'. Please check file format.")
            self.tech_specs_data = {}
        except Exception as e:
            QMessageBox.critical(self, "File Error", f"An unexpected error occurred while loading '{TECH_SPECS_FILE}':\n{e}")

    def create_tech_spec_tab(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        button_layout = QHBoxLayout()

        load_button = QPushButton("Load CSV File...")
        self.ts_input_text = QTextEdit()
        self.ts_param_id_input = QLineEdit()
        self.ts_version_id_input = QLineEdit()
        convert_button = QPushButton("Convert Data")
        clear_button = QPushButton("Clear All")
        self.ts_output_text = QTextEdit()
        copy_button = QPushButton("Copy to Clipboard")

        self.ts_output_text.setReadOnly(True)
        self.ts_output_text.setFont(QFont("Courier", 10))
        
        load_button.clicked.connect(lambda: self.load_file(self.ts_input_text))
        convert_button.clicked.connect(self.process_tech_spec_data)
        copy_button.clicked.connect(lambda: self.copy_to_clipboard(self.ts_output_text))
        clear_button.clicked.connect(self.clear_tech_spec_fields)

        form_layout.addRow(QLabel("Starting `param_id`:"), self.ts_param_id_input)
        form_layout.addRow(QLabel("Starting `version_id`:"), self.ts_version_id_input)
        button_layout.addWidget(convert_button)
        button_layout.addWidget(clear_button)
        
        layout.addWidget(load_button)
        layout.addWidget(QLabel("Paste Raw CSV Data or Load File:"))
        layout.addWidget(self.ts_input_text, 1)
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        layout.addWidget(QLabel("Formatted Tab-Separated Output:"))
        layout.addWidget(self.ts_output_text, 1)
        layout.addWidget(copy_button)
        
        self.tech_spec_tab.setLayout(layout)

    def create_model_tab(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        button_layout = QHBoxLayout()

        load_button = QPushButton("Load CSV File...")
        self.m_input_text = QTextEdit()
        self.m_version_id_input = QLineEdit()
        self.m_fabricant_id_input = QLineEdit()
        convert_button = QPushButton("Convert Model Data")
        clear_button = QPushButton("Clear All")
        self.m_output_text = QTextEdit()
        copy_button = QPushButton("Copy to Clipboard")

        self.m_output_text.setReadOnly(True)
        self.m_output_text.setFont(QFont("Courier", 10))

        load_button.clicked.connect(lambda: self.load_file(self.m_input_text))
        convert_button.clicked.connect(self.process_model_data)
        copy_button.clicked.connect(lambda: self.copy_to_clipboard(self.m_output_text))
        clear_button.clicked.connect(self.clear_model_fields)

        form_layout.addRow(QLabel("Starting `version_id`:"), self.m_version_id_input)
        form_layout.addRow(QLabel("`fabricant_id`:"), self.m_fabricant_id_input)
        button_layout.addWidget(convert_button)
        button_layout.addWidget(clear_button)

        layout.addWidget(load_button)
        layout.addWidget(QLabel("Paste Raw CSV Data or Load File (model_base,tipus,valor):"))
        layout.addWidget(self.m_input_text, 1)
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        layout.addWidget(QLabel("Formatted Tab-Separated Output:"))
        layout.addWidget(self.m_output_text, 1)
        layout.addWidget(copy_button)

        self.model_tab.setLayout(layout)

    def create_prompt_tab(self):
        layout = QVBoxLayout()
        
        prompt_label = QLabel("Use this prompt to generate the required CSV files from a PDF.")
        
        # --- Tech Spec Selection Section ---
        tech_spec_selection_layout = QVBoxLayout()
        tech_spec_selection_layout.addWidget(QLabel("<b>Select Desired Technical Specifications:</b>"))

        # Machine Type selection
        machine_type_layout = QHBoxLayout()
        machine_type_layout.addWidget(QLabel("Machine Type:"))
        self.machine_type_combo = QComboBox()
        self.machine_type_combo.currentIndexChanged.connect(self.populate_machine_subtypes)
        machine_type_layout.addWidget(self.machine_type_combo)
        tech_spec_selection_layout.addLayout(machine_type_layout)

        # Machine Sub-type selection
        machine_subtype_layout = QHBoxLayout()
        machine_subtype_layout.addWidget(QLabel("Machine Sub-type:"))
        self.machine_subtype_combo = QComboBox()
        self.machine_subtype_combo.currentIndexChanged.connect(self.populate_tech_specs_list)
        machine_subtype_layout.addWidget(self.machine_subtype_combo)
        tech_spec_selection_layout.addLayout(machine_subtype_layout)

        # Tech Specs List
        self_tech_specs_label = QLabel("Available Tech Specs:")
        self.tech_specs_list = QListWidget()
        self.tech_specs_list.setSelectionMode(QListWidget.MultiSelection) # Allow multiple selections
        tech_spec_selection_layout.addWidget(self_tech_specs_label)
        tech_spec_selection_layout.addWidget(self.tech_specs_list, 1)

        # Select/Deselect All buttons
        selection_buttons_layout = QHBoxLayout()
        select_all_button = QPushButton("Select All")
        deselect_all_button = QPushButton("Deselect All")
        select_all_button.clicked.connect(self.select_all_tech_specs)
        deselect_all_button.clicked.connect(self.deselect_all_tech_specs)
        selection_buttons_layout.addWidget(select_all_button)
        selection_buttons_layout.addWidget(deselect_all_button)
        tech_spec_selection_layout.addLayout(selection_buttons_layout)

        tech_spec_selection_layout.addSpacing(15) # Add some space

        # --- Model Specification Section ---
        model_spec_layout = QVBoxLayout()
        model_spec_layout.addWidget(QLabel("<b>Specify Models for Information Extraction (one per line):</b>"))
        self.model_input_text = QTextEdit()
        self.model_input_text.setPlaceholderText("Enter model names here, one per line (e.g., FZ 12K S, DZ 12K W MAGNUM)")
        model_spec_layout.addWidget(self.model_input_text, 1)
        layout.addLayout(model_spec_layout)
        # --- End Model Specification Section ---

        # Button to update prompt
        update_prompt_button = QPushButton("Update Prompt with Selected Specs and Models")
        update_prompt_button.clicked.connect(self.update_prompt_with_selected_specs)
        tech_spec_selection_layout.addWidget(update_prompt_button)

        layout.addLayout(tech_spec_selection_layout)
        # --- End Tech Spec Selection Section ---

        self.prompt_text_edit = QTextEdit()
        # Initial population of the prompt text (without selected specs yet)
        self.prompt_text_edit.setPlainText(PROMPT_TEXT) 
        self.prompt_text_edit.setReadOnly(True)
        self.prompt_text_edit.setFont(QFont("Helvetica", 11))
        
        copy_button = QPushButton("Copy Prompt to Clipboard")
        copy_button.clicked.connect(lambda: self.copy_to_clipboard(self.prompt_text_edit, "Prompt copied!"))

        layout.addWidget(prompt_label)
        layout.addWidget(self.prompt_text_edit)
        layout.addWidget(copy_button)
        
        self.prompt_tab.setLayout(layout)

        # Populate initial data for the combo boxes
        self.populate_machine_types()

    def populate_machine_types(self):
        """Populates the machine type combo box."""
        self.machine_type_combo.clear()
        if self.tech_specs_data:
            self.machine_type_combo.addItems(sorted(self.tech_specs_data.keys()))
        else:
            self.machine_type_combo.addItem("No machine types available")

    def populate_machine_subtypes(self):
        """Populates the machine sub-type combo box based on selected machine type."""
        self.machine_subtype_combo.clear()
        selected_type = self.machine_type_combo.currentText()
        if selected_type and selected_type in self.tech_specs_data:
            subtypes = self.tech_specs_data[selected_type]
            self.machine_subtype_combo.addItems(sorted(subtypes.keys()))
        else:
            self.machine_subtype_combo.addItem("No sub-types available")
        # Trigger population of tech specs list after sub-type is populated
        self.populate_tech_specs_list()

    def populate_tech_specs_list(self):
        """Populates the tech specs list widget based on selected machine type and sub-type."""
        self.tech_specs_list.clear()
        selected_type = self.machine_type_combo.currentText()
        selected_subtype = self.machine_subtype_combo.currentText()

        if selected_type and selected_subtype and \
           selected_type in self.tech_specs_data and \
           selected_subtype in self.tech_specs_data[selected_type]:
            
            specs = self.tech_specs_data[selected_type][selected_subtype]
            for spec in specs:
                item = QListWidgetItem(spec)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked) # Initially unchecked
                self.tech_specs_list.addItem(item)
        else:
            item = QListWidgetItem("No tech specs available for this selection.")
            item.setFlags(item.flags() & ~Qt.ItemIsUserCheckable) # Make it uncheckable
            self.tech_specs_list.addItem(item)

    def select_all_tech_specs(self):
        """Selects (checks) all items in the tech specs list."""
        for i in range(self.tech_specs_list.count()):
            item = self.tech_specs_list.item(i)
            if item.flags() & Qt.ItemIsUserCheckable: # Only check if it's a selectable item
                item.setCheckState(Qt.Checked)

    def deselect_all_tech_specs(self):
        """Deselects (unchecks) all items in the tech specs list."""
        for i in range(self.tech_specs_list.count()):
            item = self.tech_specs_list.item(i)
            if item.flags() & Qt.ItemIsUserCheckable: # Only uncheck if it's a selectable item
                item.setCheckState(Qt.Unchecked)

    def update_prompt_with_selected_specs(self):
        """
        Gathers selected tech specs and user-specified models, then appends them to the PROMPT_TEXT.
        """
        selected_specs = []
        for i in range(self.tech_specs_list.count()):
            item = self.tech_specs_list.item(i)
            if item.checkState() == Qt.Checked:
                selected_specs.append(item.text())
        
        # Construct the additional part for the tech specs in the prompt
        additional_specs_text = ""
        if selected_specs:
            additional_specs_text = "\n" + "\n".join([f"- {spec}" for spec in selected_specs])
        else:
            additional_specs_text = "\n- No specific tech specs selected. The model will try to extract relevant ones based on the general guidelines."

        # Get user-specified models
        user_models = self.model_input_text.toPlainText().strip()
        additional_models_text = ""
        if user_models:
            model_list = [model.strip() for model in user_models.split('\n') if model.strip()]
            additional_models_text = "\n\n**4. Desired Models:**\n" + "\n".join([f"- {model}" for model in model_list])
        else:
            additional_models_text = "\n\n**4. Desired Models:**\n- No specific models provided. The model should identify models from the provided PDF or search online."


        # Find the "3. Provided technical specs:" section and append
        marker_tech_specs = "**3. Provided technical specs:**"
        
        # Split the original PROMPT_TEXT at the tech specs marker
        parts_tech_specs = PROMPT_TEXT.split(marker_tech_specs, 1)

        updated_prompt = ""
        if len(parts_tech_specs) == 2:
            # Reconstruct the prompt with the selected specs appended to the correct section
            updated_prompt = parts_tech_specs[0] + marker_tech_specs + additional_specs_text
        else:
            # Fallback if marker is not found (shouldn't happen with the current PROMPT_TEXT)
            updated_prompt = PROMPT_TEXT + "\n\n" + marker_tech_specs + additional_specs_text
        
        # Now append the models section to the end of the updated prompt
        updated_prompt += additional_models_text
            
        self.prompt_text_edit.setPlainText(updated_prompt)
        QMessageBox.information(self, "Prompt Updated", "The prompt has been updated with your selected technical specifications and desired models.")


    def load_file(self, text_edit_widget):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv);;Text Files (*.txt);;All Files (*)", options=options)
        if file_name:
            try:
                with open(file_name, 'r', encoding='utf-8') as file:
                    text_edit_widget.setText(file.read())
            except Exception as e:
                QMessageBox.critical(self, "File Error", f"Could not read file:\n{e}")

    def process_tech_spec_data(self):
        # Removed .strip() from here to preserve leading/trailing blank lines if any
        raw_data = self.ts_input_text.toPlainText() 
        try:
            param_id_start = int(self.ts_param_id_input.text())
            version_id_start = int(self.ts_version_id_input.text())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter valid integer values for the starting IDs.")
            return

        if not raw_data: return

        current_param_id = param_id_start
        current_version_id = version_id_start - 1
        output_lines = []
        is_first_title = True

        for line in raw_data.split('\n'):
            stripped_line = line.strip() # Strip each line to check if it's effectively empty
            
            if not stripped_line: # If the line is empty or only contains whitespace
                output_lines.append("") # Preserve the blank line in the output
                continue # Move to the next line

            if stripped_line.startswith("Datos"):
                if not is_first_title: output_lines.append("")
                output_lines.append(stripped_line) # Use stripped_line for "Datos" entries
                current_version_id += 1
                is_first_title = False
            else:
                parts = [p.strip() for p in stripped_line.split(',')] # Strip parts as well
                if len(parts) >= 2:
                    formatted_line = f"{current_param_id}\t{current_version_id}\t{parts[0]}\t{parts[1]}\t{parts[2] if len(parts) > 2 else ''}"
                    output_lines.append(formatted_line)
                    current_param_id += 1
        
        self.ts_output_text.setPlainText("\n".join(output_lines))

    def process_model_data(self):
        raw_data = self.m_input_text.toPlainText().strip()
        try:
            version_id_start = int(self.m_version_id_input.text())
            # Removed int() conversion for fabricant_id
            fabricant_id = self.m_fabricant_id_input.text() 
        except ValueError:
            # This ValueError block is now less likely to be hit for fabricant_id
            QMessageBox.warning(self, "Input Error", "Please enter valid integer values for the IDs.")
            return

        if not raw_data: return

        current_version_id = version_id_start
        output_lines = []
        reader = csv.reader(raw_data.splitlines())

        for row in reader:
            if len(row) == 3:
                model_base, tipus, valor = row
                # Ensure fabricant_id is used as a string
                formatted_line = f"{current_version_id}\t{fabricant_id}\t{model_base.strip()}\t{tipus.strip()}\t{valor.strip()}"
                output_lines.append(formatted_line)
                current_version_id += 1
        
        self.m_output_text.setPlainText("\n".join(output_lines))

    def copy_to_clipboard(self, text_edit_widget, message="Formatted data has been copied to the clipboard."):
        QApplication.clipboard().setText(text_edit_widget.toPlainText())
        QMessageBox.information(self, "Success", message)

    def clear_tech_spec_fields(self):
        self.ts_input_text.clear()
        self.ts_output_text.clear()
        self.ts_param_id_input.clear()
        self.ts_version_id_input.clear()

    def clear_model_fields(self):
        self.m_input_text.clear()
        self.m_output_text.clear()
        self.m_version_id_input.clear()
        self.m_fabricant_id_input.clear()

# Main application entry point
if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = QWidget()
    main_layout = QVBoxLayout(main_window)
    
    data_extraction_tab = DataExtractionTab(main_window=main_window)
    main_layout.addWidget(data_extraction_tab)
    
    main_window.setWindowTitle("Data Extraction Tool")
    main_window.setGeometry(100, 100, 800, 700)
    main_window.show()
    sys.exit(app.exec_())
