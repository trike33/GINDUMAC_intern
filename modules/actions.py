import re  # <-- IMPORTANT: Added the import for regular expressions
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QGridLayout,
    QSizePolicy, QDialog, QDialogButtonBox, QScrollArea, QFrame, QTextEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class ActionPopup(QDialog):
    def __init__(self, title, text, parent=None, dark_mode=False):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(480, 420)

        # Define color palettes
        if dark_mode:
            dialog_bg = "#2E2E2E"
            title_color = "#5DADE2" # Light Blue
            content_bg = "#3C3C3C"
            text_color = "#E0E0E0" # Light Grey
        else:
            dialog_bg = "#F7F9FC" # Off-white
            title_color = "#2E86C1" # Original Blue
            content_bg = "#FFFFFF"
            text_color = "#555555" # Dark Grey

        self.setStyleSheet(f"background-color: {dialog_bg};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"color: {title_color};")
        main_layout.addWidget(title_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(10)
        content.setStyleSheet(f"background-color: {content_bg}; border-radius: 10px;")

        formatted_text = self.format_instructions(text)

        instructions = QTextEdit()
        instructions.setReadOnly(True)
        instructions.setHtml(formatted_text)
        instructions.setStyleSheet(f"""
            QTextEdit {{
                background-color: transparent;
                border: none;
                font-size: 15px;
                color: {text_color};
            }}
        """)
        content_layout.addWidget(instructions)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        # Apply theme to OK button
        ok_button = buttons.button(QDialogButtonBox.Ok)
        if ok_button:
            ok_button.setStyleSheet("""
                QPushButton {
                    min-width: 80px;
                    font-weight: bold;
                }
            """)
        main_layout.addWidget(buttons)

    def format_instructions(self, text):
        """
        Formats plain text instructions into a bulleted HTML list,
        stripping any pre-existing numbering like "1." or "2.".
        """
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        bullet_lines = []
        bullet_emoji = "•"  # You can replace this with "👉" or "✔️"
        
        for line in lines:
            # --- THIS IS THE FIX ---
            # Use a regular expression to find lines starting with numbers and a period.
            # Example: matches "1.", "12. ", " 3.  " etc.
            match = re.match(r'^\s*\d+\.\s*', line)
            
            # If a match is found, remove that part from the line
            if match:
                line = line[len(match.group(0)):].strip()
            # --- END OF FIX ---
            
            bullet_lines.append(f"{bullet_emoji} {line}")
            
        # Join lines with <br> tags for HTML formatting
        return "<br><br>".join(bullet_lines)


class ActionsTab(QWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window # Store the reference

        layout = QVBoxLayout(self)
        title = QLabel("<h2 style='color: #2F4F4F;'>Available Actions</h2>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(20)

        actions = [
            ("Leads Template",
             """📋 Ve a Borja Smart list.
             ✅ Asegúrate que el estado sea 'enquiry-received' y la fecha sea -1 día hábil.
             ✉️ Copia el correo en el cuadro de texto; la plantilla se generará y copiará automáticamente.
             ⚠️ Si ocurre algún problema, la aplicación mostrará un error y no copiará una plantilla errónea."""),

            ("Leads I-Sent",
             """🔎 Ve a la pestaña 'Leads I-sent'.
             🌍 Selecciona el idioma (inglés, italiano o francés) para copiar la plantilla de seguimiento.
             📋 Pega la plantilla en el correo de seguimiento para el cliente.
             🔗 Si tienes URLs nuevas, añádelas en el cuadro de texto y guárdalas."""),

            ("Contacts",
             """👥 Ve a la pestaña 'Contacts'.
             📂 Selecciona el archivo CSV de contactos que quieres procesar.
             ➡️ Haz clic en 'Initialize Process' para cargar los datos.
             🖱️ Usa el botón 'Copy Next Email' para obtener cada correo de seguimiento de forma secuencial."""),
            
            ("Metabase",
             """📊 Ve a la pestaña 'Metabase'.
             ⚙️ Rellena los detalles de la máquina (Precio, Link, Nombre) y selecciona el archivo CSV de Metabase.
             ▶️ Haz clic en 'Initialize Process'.
             📋 Usa 'Copy Next Email' para generar y copiar cada correo para los leads."""),

            ("HTML2Text",
             """🔠 Ve a la pestaña 'HTML2Text'.
             🌐 Pega una o más URLs en el cuadro de texto.
             🔑 Opcionalmente, introduce una palabra clave para buscar un tipo de etiqueta específico en la primera URL.
             🖱️ Procesa cada URL una por una para extraer el texto limpio."""),

            ("Statistics",
             """📈 La pestaña 'Statistics' muestra un resumen de las acciones realizadas.
             🔄 Los contadores se actualizan automáticamente cada vez que copias una plantilla o procesas un correo.
             👀 Úsalo para llevar un registro de tu trabajo diario."""),
            ("Machine data prompt",
                """For each machine, provide:
    Application Type (1–38):
    EDM, Grinding, Measuring, Milling, Sawing, Turning, Shearing, Injection Moulding, 3D Printing, Robotics, Blow Moulding, Compounding, Extrusion, CNC Wood Machining, Boring & Drilling (Wood), Profiling, Milling (Wood), Veneering, Planing, Edge Banding, Pressing/Laminating, Sawing (Wood), Sanding, Complete Production, Other Woodworking Machinery, Other Automation Equipment, Other Plastic Processing Machinery, Cutting, Punching, Stamping, Forming, Rolling, Other Sheet Metal Machinery, Broaching, Honing, Shaping & Planing, Other Machine Tools, Bending

    Machine Type (1–131):
    e.g. Waterjet Cutting Machine, Metal Band Saw, Wood Band Saw, Circular Saw (Wood/Metal), Planer, Blow Moulding Machine, Extruder (Film, Twin/Single Screw, Pipe, Profile, Sheet, Co), CNC Router, CNC Wood Machining Centre, Wood Boring Machine, Spindle Moulder, Profile Grinder, Mill (Wood), Press (Briquetting, Carcase, Laminating, Veneer), Mitre/Table/Panel Saw, Sander (Belt/Drum), Production Line (Wood), Chipper, Moulder, Deburring Machine, Laser (Welding, Marking, Engraving, CO2), Robot (Arm, Delta, Welding, Collaborative, Gantry), Automation Equipment, Injection Moulding (Vertical, Electrical, Hydraulic), Compounder, Recycling Machine, Moulding Machine (Foam, Rotational), Thermoformer, Granulator, Tube Cutting, Press Brake, Hydraulic/Mechanical/Stamping Press, CNC Punch (Turret, Press), Punch-Laser Combo, Shearing Machine (Hydraulic/CNC), Rolling Machine (Plate, Angle, Section), Stretch/Forming, Edge Rounding, Machining Centres (Vertical, Horizontal, Universal), Milling (CNC, Gantry), Turn-Mill, Turning (Vertical, Horizontal, Multi-Spindle), Grinding (Surface, Centerless, Cylindrical, Internal, Horizontal, Vertical), 3D Printer (Metal/Plastic), EDM (Wire, Die-Sinking), Measuring Machine (CMM, Optical, Laser), Saw (Hack), Broaching (Horizontal, Vertical), Honing (Horizontal, Vertical), Drilling/Boring Machine (Metal), Machine Tool, Punching & Bending Machine

    Control Unit Brand (1–47):
    ABB, AGIE, AMADA, ARBURG, BATTENFELD, BECKHOFF, BIESSE, BODOR, BOSCH, BOSCHERT, BROTHER, BYSTRONIC, CADMAN, CHARMILLES, CINCOM, CYBELEC, DELEM, EMCO, ENGEL, ESAB, FAGOR, FANUC, FIDIA, HAAS, HACO, HAITIAN, HEIDENHAIN, HURCO, INDEX, KRAUSS MAFFEI, KUKA, MAKINO, MATSUURA, MAZATROL, MicroStep, MITSUBISHI, NETSTAL, OKUMA, PRIMA POWER, RÖDERS, SELCA, SIEMENS, SODICK, TRAUB, TRUMPF, ZEISS, Other

    Control Unit Model

    Number of Axis""")
        ]

        btn_style = """
            QPushButton {
                background-color: #5A9BD5; border-radius: 10px; color: white;
                font-weight: bold; font-size: 16px; padding: 15px 30px;
            }
            QPushButton:hover { background-color: #4A89C4; }
            QPushButton:pressed { background-color: #3A6B99; }
        """

        for i, (text, popup_text) in enumerate(actions):
            btn = QPushButton(text)
            btn.setToolTip(popup_text)
            btn.setStyleSheet(btn_style)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            btn.setMinimumHeight(60)
            btn.clicked.connect(lambda checked, t=text, p=popup_text: self.open_action_window(t, p))
            grid.addWidget(btn, i // 3, i % 3)

        layout.addLayout(grid)
        layout.addStretch()

    def open_action_window(self, title, text):
            # Check if dark mode is active in the main window
            dark_mode_active = self.main_window.is_dark_mode if self.main_window else False
            dialog = ActionPopup(title, text, self, dark_mode=dark_mode_active)
            dialog.exec_()

