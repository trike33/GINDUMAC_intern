import sys
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from calendar import monthrange
import os
from fpdf import *
import re

from PyQt5.QtWidgets import (
    QApplication, QWidget, QMainWindow, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTabWidget, QFormLayout, QDialog,
    QToolTip, QDateEdit, QMessageBox, QComboBox, QMenuBar,QAction, QTextEdit
    )
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtGui import QPainter, QCursor
from PyQt5.QtChart import (
    QChartView, QChart, QPieSeries, QPieSlice,
    QBarSet, QBarSeries, QBarCategoryAxis, QValueAxis,
    QLineSeries
)

DATA_FILE = Path("stats_progress.json")


def clean_text_for_pdf(text):
    # Eliminar todos los caracteres que no sean ASCII imprimibles
    return re.sub(r'[^\x00-\x7F]+', '', text)

class ConclusionsWindow(QDialog):
    def __init__(self, stats_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 Conclusiones Estadísticas Avanzadas")
        self.resize(600, 500)

        self.stats_data = stats_data

        layout = QVBoxLayout(self)

        title = QLabel("<h2 style='color:#2F4F4F;'>Conclusiones y Reporte Estadístico</h2>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.conclusions_area = QTextEdit()
        self.conclusions_area.setReadOnly(True)
        self.conclusions_area.setStyleSheet("font-family: 'Courier New', monospace; font-size: 14px;")
        layout.addWidget(self.conclusions_area)

        btn_generate = QPushButton("📈 Generar Conclusiones")
        btn_generate.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        btn_generate.clicked.connect(self.generate_conclusions)
        layout.addWidget(btn_generate)

        btn_export_pdf = QPushButton("📄 Exportar Reporte PDF")
        btn_export_pdf.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 10px;")
        btn_export_pdf.clicked.connect(self.export_pdf)
        layout.addWidget(btn_export_pdf)

    def generate_conclusions(self):
        print("DEBUG stats_data:", self.stats_data)

        if not self.stats_data:
            self.conclusions_area.setPlainText("⚠️ No hay datos para analizar.")
            return
        
        intro = (
            "📋 Informe Estadístico Profesional\n\n"
            "Este informe presenta un análisis detallado de las métricas clave recogidas. "
            "Se ofrecen interpretaciones y objetivos para facilitar la toma de decisiones.\n\n"
        )

        kpi_info = {
            "Template Leads": {
                "interpretation": "Cantidad de plantillas de leads generadas correctamente.",
                "optimal": "Mayor a 15 por día para mantener un flujo saludable de nuevos leads."
            },
            "Email-Sent": {
                "interpretation": "Número de emails enviados con leads confirmados.",
                "optimal": "Idealmente más de 12 por día para un buen seguimiento comercial."
            },
            "Contacts": {
                "interpretation": "Cantidad de contactos procesados y validados.",
                "optimal": "Debería superar los 8 contactos diarios para mantener actualizada la base de datos."
            },
            "Metabase": {
                "interpretation": "Consultas y reportes generados en Metabase.",
                "optimal": "Más de 5 consultas diarias indican un análisis continuo del rendimiento."
            },
        }

        # Aquí vamos a crear un dict para juntar todos los valores por métrica
        metric_values = {}

        # Recorremos fechas y métricas internas para agrupar valores por cada métrica
        for date, metrics_dict in self.stats_data.items():
            for metric, value in metrics_dict.items():
                try:
                    num = float(value)
                except (ValueError, TypeError):
                    continue
                metric_values.setdefault(metric, []).append(num)

        if not metric_values:
            self.conclusions_area.setPlainText("⚠️ No hay datos numéricos válidos para analizar.")
            return

        detalles = ""
        for metric, values in metric_values.items():
            n = len(values)
            media = sum(values) / n
            minimum = min(values)
            maximum = max(values)
            variance = sum((x - media) ** 2 for x in values) / n
            std_dev = variance ** 0.5
            kpi_performance = media * 1.15  # KPI ajustado como ejemplo

            info = kpi_info.get(metric, {})
            interpretation = info.get("interpretation", "No hay interpretación disponible.")
            optimal = info.get("optimal", "No hay valor óptimo definido.")

            detalles += (
                f"📊 {metric}:\n"
                f"  - Número de datos analizados: {n}\n"
                f"  - Media: {media:.2f}\n"
                f"  - Mínimo: {minimum}\n"
                f"  - Máximo: {maximum}\n"
                f"  - Desviación Estándar: {std_dev:.2f}\n"
                f"  - KPI de Performance Estimado: {kpi_performance:.2f}\n"
                f"  - Interpretación: {interpretation}\n"
                f"  - Valor óptimo/meta: {optimal}\n\n"
            )

        conclusions = (
            "🔎 Conclusiones y Recomendaciones Generales:\n"
            "- Mantener seguimiento continuo para detectar tendencias o anomalías.\n"
            "- Analizar cualquier desviación significativa para tomar medidas correctivas.\n"
            "- Ajustar procesos internos para alcanzar o superar los valores óptimos.\n"
            "- Realizar reportes periódicos para informar a los stakeholders.\n"
        )

        full_report = intro + detalles + conclusions

        print("DEBUG full report:\n", full_report)  # Para verificar que el texto final está OK

        self.conclusions_area.setPlainText(full_report)

    def export_pdf(self):
        if self.conclusions_area.toPlainText().strip() == "":
            self.conclusions_area.setText("⚠️ Por favor, genera las conclusiones antes de exportar el PDF.")
            return

        pdf = FPDF()
        pdf.add_page()

        # Título
        pdf.set_font("Arial", 'B', 16)
        pdf.set_text_color(47, 79, 79)  # Dark slate gray
        pdf.cell(0, 10, "Reporte de Conclusiones Estadísticas", ln=True, align="C")
        pdf.ln(10)

        # Subtítulo
        pdf.set_font("Arial", 'B', 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, "Resumen de KPIs y Recomendaciones", ln=True)
        pdf.ln(5)

        # Obtener y limpiar texto para PDF
        raw_text = self.conclusions_area.toPlainText()
        clean_text = clean_text_for_pdf(raw_text)

        # Parsear texto para mejor formato en PDF
        lines = clean_text.split('\n')

        pdf.set_font("Courier", size=12)
        for line in lines:
            if line.startswith("Estadísticas Generales") or line.startswith("Recomendaciones") or line.startswith("----------------"):
                # Headers o separadores en negrita
                pdf.set_font("Courier", 'B', 12)
            else:
                pdf.set_font("Courier", size=12)
            pdf.multi_cell(0, 8, line)
        pdf.ln(10)

        # Footer con página
        pdf.set_y(-15)
        pdf.set_font('Arial', 'I', 8)
        pdf.set_text_color(128, 128, 128)
        pdf.cell(0, 10, 'Página %s' % pdf.page_no(), 0, 0, 'C')

        filename = "reporte_estadisticas_profesional.pdf"
        pdf.output(filename)

        self.conclusions_area.append("\n✅ Reporte PDF generado con éxito como:\n" + filename)

class StatsGraphWindow(QDialog):
    def __init__(self, stats_dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Graphical Statistics (Latest Entry Summary)")
        self.resize(1200, 700)

        layout = QHBoxLayout(self)

        # Get the latest date
        if not stats_dict:
            return
        last_date = max(stats_dict.keys())
        cumulative = {}
        for date, daily in stats_dict.items():
            for stat, val in daily.items():
                try:
                    cumulative[stat] = cumulative.get(stat, 0) + float(val)
                except ValueError:
                    continue

        # PIE CHART
        self.pie_series = QPieSeries()
        self.slice_map = {}

        for label, value in cumulative.items():
            if value > 0:
                pie_slice = self.pie_series.append(label, value)
                self.slice_map[pie_slice] = (label, value)
                pie_slice.setLabelVisible(False)
                pie_slice.hovered.connect(self.on_hover_slice)

        pie_chart = QChart()
        pie_chart.addSeries(self.pie_series)
        pie_chart.setTitle(f"Pie Chart - Totals up to {last_date}")
        pie_chart.legend().setVisible(True)
        pie_chart.legend().setAlignment(Qt.AlignBottom)

        pie_view = QChartView(pie_chart)
        pie_view.setRenderHint(QPainter.Antialiasing)
        layout.addWidget(pie_view)

        # BAR CHART
        bar_set = QBarSet("Total")
        categories = []
        values = []

        for label, value in cumulative.items():
            categories.append(label)
            values.append(value)

        bar_set.append(values)
        bar_series = QBarSeries()
        bar_series.append(bar_set)

        bar_chart = QChart()
        bar_chart.addSeries(bar_series)
        bar_chart.setTitle(f"Bar Chart - Totals up to {last_date}")
        bar_chart.setAnimationOptions(QChart.SeriesAnimations)

        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        bar_chart.addAxis(axis_x, Qt.AlignBottom)
        bar_series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, max(values) * 1.2 if values else 10)
        bar_chart.addAxis(axis_y, Qt.AlignLeft)
        bar_series.attachAxis(axis_y)

        bar_chart.legend().setVisible(False)
        bar_view = QChartView(bar_chart)
        bar_view.setRenderHint(QPainter.Antialiasing)
        layout.addWidget(bar_view)

    def on_hover_slice(self, state):
        slice = self.sender()
        if not isinstance(slice, QPieSlice):
            return
        label, value = self.slice_map.get(slice, ("Unknown", 0))
        total = sum(val for _, val in self.slice_map.values())
        percent = (value / total) * 100 if total > 0 else 0
        if state:
            QToolTip.showText(QCursor.pos(), f"{label}: {percent:.1f}% ({value})")
        else:
            QToolTip.hideText()


class ProgressGraphWindow(QDialog):
    def __init__(self, stats_data, stats_keys, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Progress Over Time")
        self.resize(1000, 600)

        self.stats_data = stats_data  # dict date_str -> {stat: value}
        self.stats_keys = stats_keys

        self.current_unit = "Weeks"  # default unit
        self.current_period_start = None  # will hold date for period start

        self.init_ui()


    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Menu bar (optional, can keep or remove)
        self.menu_bar = QMenuBar()
        main_layout.setMenuBar(self.menu_bar)
        view_menu = self.menu_bar.addMenu("View")
        self.action_days = QAction("Days", self)
        self.action_weeks = QAction("Weeks", self)
        self.action_months = QAction("Months", self)
        view_menu.addAction(self.action_days)
        view_menu.addAction(self.action_weeks)
        view_menu.addAction(self.action_months)
        self.action_days.triggered.connect(lambda: self.change_unit("Days"))
        self.action_weeks.triggered.connect(lambda: self.change_unit("Weeks"))
        self.action_months.triggered.connect(lambda: self.change_unit("Months"))

        # Controls layout: unit combo + navigation buttons + period label
        controls_layout = QHBoxLayout()

        controls_layout.addWidget(QLabel("Select Unit:"))
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["Days", "Weeks", "Months"])
        self.unit_combo.setCurrentText(self.current_unit)
        self.unit_combo.currentTextChanged.connect(self.change_unit)
        controls_layout.addWidget(self.unit_combo)

        self.prev_btn = QPushButton("<< Prev")
        self.next_btn = QPushButton("Next >>")
        self.period_label = QLabel("")

        self.prev_btn.clicked.connect(self.go_prev)
        self.next_btn.clicked.connect(self.go_next)

        controls_layout.addWidget(self.prev_btn)
        controls_layout.addWidget(self.period_label)
        controls_layout.addWidget(self.next_btn)

        main_layout.addLayout(controls_layout)

        # Chart view
        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        main_layout.addWidget(self.chart_view)

        self.setLayout(main_layout)

        # Initialize period start to earliest date in data or today
        if self.stats_data:
            all_dates = sorted(datetime.strptime(d, "%Y-%m-%d").date() for d in self.stats_data.keys())
            self.current_period_start = all_dates[0]
        else:
            self.current_period_start = date.today()

        self.update_chart()

    def change_unit(self, unit):
        self.current_unit = unit
        # Reset current period start to earliest date or today on unit change
        if self.stats_data:
            all_dates = sorted(datetime.strptime(d, "%Y-%m-%d").date() for d in self.stats_data.keys())
            self.current_period_start = all_dates[0]
        else:
            self.current_period_start = date.today()
        self.update_chart()
        self.unit_combo.setCurrentText(unit)

    def go_prev(self):
        if self.current_unit == "Days":
            self.current_period_start -= timedelta(days=1)
        elif self.current_unit == "Weeks":
            self.current_period_start -= timedelta(weeks=1)
        elif self.current_unit == "Months":
            year = self.current_period_start.year
            month = self.current_period_start.month - 1
            if month < 1:
                month = 12
                year -= 1
            self.current_period_start = self.current_period_start.replace(year=year, month=month, day=1)
        self.update_chart()

    def go_next(self):
        if self.current_unit == "Days":
            self.current_period_start += timedelta(days=1)
        elif self.current_unit == "Weeks":
            self.current_period_start += timedelta(weeks=1)
        elif self.current_unit == "Months":
            year = self.current_period_start.year
            month = self.current_period_start.month + 1
            if month > 12:
                month = 1
                year += 1
            self.current_period_start = self.current_period_start.replace(year=year, month=month, day=1)
        self.update_chart()

    def update_chart(self):
        # Show aggregated stats only for the current period (day/week/month)
        aggregation = {stat: 0 for stat in self.stats_keys}

        # Calculate period range start/end based on unit and current_period_start
        start = self.current_period_start
        if self.current_unit == "Days":
            end = start
            period_label = start.strftime("%Y-%m-%d")
        elif self.current_unit == "Weeks":
            start = start - timedelta(days=start.weekday())  # Monday start
            end = start + timedelta(days=6)
            period_label = f"Week {start.isocalendar()[1]} ({start.strftime('%b %d')}–{end.strftime('%b %d')})"
        else:  # Months
            start = start.replace(day=1)
            last_day = monthrange(start.year, start.month)[1]
            end = start.replace(day=last_day)
            period_label = start.strftime("%B %Y")

        self.period_label.setText(period_label)

        # Aggregate data only within this period
        for date_str, stats in self.stats_data.items():
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d").date()
            except:
                continue
            if start <= dt <= end:
                for stat in self.stats_keys:
                    try:
                        val = float(stats.get(stat, 0))
                    except:
                        val = 0
                    aggregation[stat] += val

        # Now build chart with this aggregation (1 bar per stat, or line with 1 point per stat)
        chart = QChart()
        chart.setTitle(f"Progress: {period_label}")

        bar_set = QBarSet("Total")
        categories = []
        values = []

        for stat, val in aggregation.items():
            categories.append(stat)
            values.append(val)

        bar_set.append(values)
        bar_series = QBarSeries()
        bar_series.append(bar_set)
        chart.addSeries(bar_series)

        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.addAxis(axis_x, Qt.AlignBottom)
        bar_series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, max(values)*1.2 if values else 10)
        chart.addAxis(axis_y, Qt.AlignLeft)
        bar_series.attachAxis(axis_y)

        chart.legend().setVisible(False)

        self.chart_view.setChart(chart)

class StatisticsTab(QWidget):
    output_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.stats_keys = ["Template Leads", "Email-Sent", "Contacts", "Metabase"]
        self.stats_data = {}  # dict date_str -> {stat: value}
        self.current_date = date.today()
        self.init_ui()
        self.load_data()
        self.update_ui_for_date(self.current_date)
        self.stats_file = "stats_progress.json"

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("📊 Manual Statistics Entry"))

        # Date picker
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Select Date:"))
        self.date_edit = QDateEdit(calendarPopup=True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.dateChanged.connect(self.on_date_changed)
        date_layout.addWidget(self.date_edit)
        layout.addLayout(date_layout)

        # Form for stats inputs
        self.inputs = {}
        form = QFormLayout()
        for stat in self.stats_keys:
            le = QLineEdit()
            le.setPlaceholderText("Enter number")
            self.inputs[stat] = le
            form.addRow(f"{stat}:", le)
        layout.addLayout(form)

        # Buttons layout
        btn_layout = QHBoxLayout()

        self.save_btn = QPushButton("💾 Save Entry")
        self.save_btn.clicked.connect(self.save_current_entry)
        btn_layout.addWidget(self.save_btn)

        delete_btn = QPushButton("🗑️ Delete Stats")
        delete_btn.clicked.connect(self.delete_stats)
        btn_layout.addWidget(delete_btn)

        self.show_chart_btn = QPushButton("📈 Show Graphical Stats")
        self.show_chart_btn.clicked.connect(self.show_chart)
        btn_layout.addWidget(self.show_chart_btn)

        self.show_progress_btn = QPushButton("📅 Show Progress Over Time")
        self.show_progress_btn.clicked.connect(self.show_progress)
        btn_layout.addWidget(self.show_progress_btn)

        # Botón para generar conclusiones
        self.btn_generate = QPushButton("🎯 Conclusiones")
        self.btn_generate.clicked.connect(self.open_conclusions_window)
        btn_layout.addWidget(self.btn_generate)

        layout.addLayout(btn_layout)

    def open_conclusions_window(self):
        dialog = ConclusionsWindow(self.stats_data, self)
        dialog.exec_()

    def delete_stats(self):
        if not os.path.exists(self.stats_file):
            QMessageBox.information(self, "No File", "Stats file does not exist.")
            return

        confirm = QMessageBox.question(
            self,
            "Delete File?",
            f"Are you sure you want to delete '{self.stats_file}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            try:
                os.remove(self.stats_file)
                self.stats_data.clear()
                QMessageBox.information(self, "Deleted", "Stats file deleted successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not delete file: {e}")


    def on_date_changed(self, qdate):
        py_date = qdate.toPyDate()
        self.current_date = py_date
        self.update_ui_for_date(py_date)
        self.output_message.emit(f"[StatisticsTab] Date changed to {py_date}\n")

    def update_ui_for_date(self, dt):
        date_str = dt.isoformat()
        stats_for_date = self.stats_data.get(date_str, {})
        for stat in self.stats_keys:
            val = stats_for_date.get(stat, "")
            self.inputs[stat].setText(str(val))

    def save_current_entry(self):
        date_str = self.current_date.isoformat()
        entry = {}
        for stat, le in self.inputs.items():
            val = le.text().strip()
            if val == "":
                val = "0"
            try:
                float(val)
            except ValueError:
                QMessageBox.warning(self, "Invalid input", f"Invalid number for {stat}: {val}")
                return
            entry[stat] = val

        self.stats_data[date_str] = entry
        self.save_data()
        self.output_message.emit(f"[StatisticsTab] Saved stats for {date_str}: {entry}\n")

    def show_chart(self):
        self.output_message.emit(f"[StatisticsTab] Showing full graph from data: {self.stats_data}\n")
        graph_window = StatsGraphWindow(self.stats_data, self)
        graph_window.exec_()


    def show_progress(self):
        # Open the progress over time window
        progress_window = ProgressGraphWindow(self.stats_data, self.stats_keys, self)
        progress_window.exec_()

    def save_data(self):
        try:
            with open(DATA_FILE, "w") as f:
                json.dump(self.stats_data, f, indent=2)
        except Exception as e:
            self.output_message.emit(f"[StatisticsTab] Error saving data: {e}\n")

    def load_data(self):
        if DATA_FILE.exists():
            try:
                with open(DATA_FILE, "r") as f:
                    self.stats_data = json.load(f)
            except Exception as e:
                self.output_message.emit(f"[StatisticsTab] Error loading data: {e}\n")
                self.stats_data = {}
        else:
            self.stats_data = {}


class TestMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Statistics Progress Tracker")
        self.setGeometry(300, 200, 800, 600)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Statistics tab (input + aggregated chart + progress popup)
        self.stats_tab = StatisticsTab()
        self.stats_tab.output_message.connect(self.print_output)
        self.tabs.addTab(self.stats_tab, "📊 Statistics")

    def print_output(self, msg):
        print(msg.strip())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestMainWindow()
    window.show()
    sys.exit(app.exec_())
