import sys
import csv
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QLabel, QLineEdit, QFormLayout, QMessageBox,
    QFileDialog, QTabWidget
)
from PyQt5.QtGui import QFont

# --- Prompt Text ---
# The prompt for generating CSV data is stored here as a constant.
PROMPT_TEXT = """Based on the provided PDF brochure, generate two distinct CSV outputs in two separate, single code blocks.

**1. Model Information CSV:**

First, create a CSV file that lists the machine models. The output must strictly follow the format: `model_base,tipus_clasificador,valor_clasificador`.

- Identify every unique machine model from the column headers in the "Technical data" tables within the PDF.
- The `model_base` should be the main series name (e.g., "CHIRON 12 Series").
- The `tipus_clasificador` for all these entries will be "Model".
- The `valor_clasificador` will be the full model name (e.g., "FZ 12K S", "DZ 12K W MAGNUM", etc.).

**2. Technical Specifications CSV:**

Second, create a more detailed CSV of the technical specifications. Your primary goal is to map the data from the PDF to the standardized parameter names and units listed below.

- For each machine model, begin with a title line in the format: `Datos [Full Model Name]`.
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
"""

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
        self.prompt_text_edit = QTextEdit()
        self.prompt_text_edit.setPlainText(PROMPT_TEXT)
        self.prompt_text_edit.setReadOnly(True)
        self.prompt_text_edit.setFont(QFont("Helvetica", 11))
        
        copy_button = QPushButton("Copy Prompt to Clipboard")
        copy_button.clicked.connect(lambda: self.copy_to_clipboard(self.prompt_text_edit, "Prompt copied!"))

        layout.addWidget(prompt_label)
        layout.addWidget(self.prompt_text_edit)
        layout.addWidget(copy_button)
        
        self.prompt_tab.setLayout(layout)

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
        raw_data = self.ts_input_text.toPlainText().strip()
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
            line = line.strip()
            if not line: continue
            if line.startswith("Datos"):
                if not is_first_title: output_lines.append("")
                output_lines.append(line)
                current_version_id += 1
                is_first_title = False
            else:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 2:
                    formatted_line = f"{current_param_id}\t{current_version_id}\t{parts[0]}\t{parts[1]}\t{parts[2] if len(parts) > 2 else ''}"
                    output_lines.append(formatted_line)
                    current_param_id += 1
        
        self.ts_output_text.setPlainText("\n".join(output_lines))

    def process_model_data(self):
        raw_data = self.m_input_text.toPlainText().strip()
        try:
            version_id_start = int(self.m_version_id_input.text())
            fabricant_id = int(self.m_fabricant_id_input.text())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter valid integer values for the IDs.")
            return

        if not raw_data: return

        current_version_id = version_id_start
        output_lines = []
        reader = csv.reader(raw_data.splitlines())

        for row in reader:
            if len(row) == 3:
                model_base, tipus, valor = row
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

