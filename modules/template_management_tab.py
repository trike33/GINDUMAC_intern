# modules/template_management_tab.py

import os
import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QGroupBox, 
                             QPushButton, QComboBox, QMessageBox, QLabel, QDialog)
from PyQt5.QtCore import pyqtSignal

# Importa los diálogos del nuevo módulo de gestores
from .managers import TemplateManagerDialog, RuleManagerDialog

class TemplateManagementTab(QWidget):
    output_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Diccionario central de archivos a gestionar
        self.target_files = {
            "Leads Templates": ("templates/leads_templates.json", "template"),
            "Contacts Templates": ("templates/contacts_templates.json", "template"),
            "Metabase Templates": ("templates/metabase_templates.json", "template"),
            "I-sent Templates": ("templates/isent_templates.json", "template"),
            "Leads Parsing Rules": ("regex/parsing_rules.json", "rule")
        }

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        control_group = QGroupBox("Select a file to manage")
        form_layout = QFormLayout(control_group)

        self.file_selector_combo = QComboBox()
        self.file_selector_combo.addItems(self.target_files.keys())
        
        manage_button = QPushButton("Manage Selected File")
        manage_button.clicked.connect(self.open_manager)

        form_layout.addRow(QLabel("Target File:"), self.file_selector_combo)
        form_layout.addRow(manage_button)
        
        main_layout.addWidget(control_group)
        main_layout.addStretch(1)
        self.setLayout(main_layout)

    def open_manager(self):
        selection_key = self.file_selector_combo.currentText()
        file_path, file_type = self.target_files[selection_key]

        # Cargar los datos del archivo JSON
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Crear una estructura por defecto si el archivo no existe o está vacío
            data = {} if file_type == 'template' else []
            self.output_message.emit(f"[Manager] '{file_path}' not found or empty. Using default structure.\n")

        # Abrir el diálogo apropiado
        if file_type == 'template':
            dialog = TemplateManagerDialog(data, self)
        else: # 'rule'
            dialog = RuleManagerDialog(data, self)

        if dialog.exec_() == QDialog.Accepted:
            # Si se aceptan los cambios, guardar los datos actualizados
            updated_data = dialog.get_updated_templates() if file_type == 'template' else dialog.get_updated_rules()
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(updated_data, f, indent=2, ensure_ascii=False)
                self.output_message.emit(f"[Manager] Successfully updated '{file_path}'.\n")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save file '{file_path}':\n{e}")
