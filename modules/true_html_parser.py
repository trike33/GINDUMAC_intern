import sys
import requests
from bs4 import BeautifulSoup, NavigableString
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QProgressBar, QLabel, QMainWindow, QMessageBox,
    QLineEdit, QComboBox, QStackedWidget
)
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot

# --- Stylesheet for a Modern Dark Theme ---
DARK_STYLESHEET = """
QWidget {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 14px;
    background-color: #2c3e50;
    color: #ecf0f1;
}
QMainWindow {
    background-color: #2c3e50;
}
QLabel {
    font-weight: bold;
    color: #1abc9c;
    padding-bottom: 5px;
}
QTextEdit, QLineEdit, QComboBox {
    background-color: #34495e;
    border: 1px solid #4a627a;
    border-radius: 5px;
    padding: 8px;
    color: #ecf0f1;
}
QComboBox {
    padding: 6px 8px;
}
QComboBox::drop-down {
    border: none;
}
QComboBox::down-arrow {
    image: url(down_arrow.png); /* A placeholder, Qt will use a default if not found */
}
QPushButton {
    background-color: #1abc9c;
    color: white;
    border: none;
    padding: 10px 15px;
    border-radius: 5px;
    font-weight: bold;
}
QPushButton#resetButton {
    background-color: #3498db;
}
QPushButton#resetButton:hover {
    background-color: #2980b9;
}
QPushButton:hover {
    background-color: #16a085;
}
QPushButton:disabled {
    background-color: #95a5a6;
    color: #bdc3c7;
}
QProgressBar {
    border: 1px solid #4a627a;
    border-radius: 5px;
    text-align: center;
    color: #ecf0f1;
    background-color: #34495e;
}
QProgressBar::chunk {
    background-color: #1abc9c;
    border-radius: 4px;
}
QMessageBox {
    background-color: #34495e;
}
"""

# --- Worker for Network Operations ---
class Worker(QObject):
    """
    Performs network requests and HTML parsing in a separate thread.
    """
    finished = pyqtSignal(str, str)
    error = pyqtSignal(str)

    @pyqtSlot(str, str, str)
    def process_url(self, url, user_input, target_tag_name):
        """
        Fetches a URL and parses it based on a keyword or tag name.
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            body = soup.find('body')

            if not body:
                self.error.emit(f"Could not find a <body> tag in the page at {url}.")
                return

            discovered_tag = ""
            if not target_tag_name:
                if not user_input:
                    text_content = body.get_text(separator='\n', strip=True)
                    self.finished.emit(text_content, "")
                    return
                
                found_text_node = body.find(string=lambda text: isinstance(text, NavigableString) and user_input.lower() in text.lower())
                if not found_text_node or not hasattr(found_text_node.parent, 'name'):
                    self.error.emit(f"Keyword '{user_input}' not found or its parent tag could not be determined in {url}.")
                    return
                
                target_tag_name = found_text_node.parent.name
                discovered_tag = target_tag_name

            all_similar_tags = body.find_all(target_tag_name)
            if not all_similar_tags:
                self.error.emit(f"No <{target_tag_name}> tags were found in {url}.")
                return

            extracted_texts = [tag.get_text(separator='\n', strip=True) for tag in all_similar_tags]
            final_text = "\n\n---\n\n".join(extracted_texts)
            
            self.finished.emit(f"Extracted text from {len(all_similar_tags)} <{target_tag_name}> tags:\n\n{final_text}", discovered_tag)

        except requests.exceptions.RequestException as e:
            self.error.emit(f"Network Error for {url}:\n{str(e)}")
        except Exception as e:
            self.error.emit(f"An unexpected error occurred for {url}:\n{str(e)}")


# --- Main Application Widget ---
class HtmlToTextTab(QWidget):
    """
    A portable widget that provides a UI for converting a list of URLs
    to plain text, using a consistent tag across all URLs.
    """
    request_process_url = pyqtSignal(str, str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.urls_to_process = []
        self.current_url_index = -1
        self.is_running = False
        self.target_tag_name = ""
        
        self.init_ui()
        self.init_worker_thread()

    def init_ui(self):
        """ Sets up the user interface layout and widgets. """
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        url_label = QLabel("Enter URLs (one per line):")
        self.url_input_area = QTextEdit()
        self.url_input_area.setPlaceholderText("https://example.com/page1\nhttps://example.com/page2")
        main_layout.addWidget(url_label)
        main_layout.addWidget(self.url_input_area)

        mode_label = QLabel("Select Extraction Mode:")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Find Tag by Keyword (on 1st URL)", "Specify HTML Tag Directly"])
        
        self.input_stack = QStackedWidget()
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("Enter keyword to find in the first URL...")
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("e.g., h2, p, div")
        
        self.input_stack.addWidget(self.keyword_input)
        self.input_stack.addWidget(self.tag_input)
        self.mode_combo.currentIndexChanged.connect(self.input_stack.setCurrentIndex)
        
        main_layout.addWidget(mode_label)
        main_layout.addWidget(self.mode_combo)
        main_layout.addWidget(self.input_stack)

        controls_layout = QHBoxLayout()
        self.process_button = QPushButton("Start Processing")
        self.process_button.clicked.connect(self.handle_button_click)
        self.reset_button = QPushButton("Reset")
        self.reset_button.setObjectName("resetButton")
        self.reset_button.clicked.connect(self.reset_state)
        self.reset_button.hide()
        self.progress_bar = QProgressBar()
        controls_layout.addWidget(self.process_button)
        controls_layout.addWidget(self.reset_button)
        controls_layout.addWidget(self.progress_bar)
        main_layout.addLayout(controls_layout)

        output_label = QLabel("Extracted Text:")
        self.output_text_area = QTextEdit()
        self.output_text_area.setReadOnly(True)
        self.output_text_area.setPlaceholderText("Text from the processed webpage will appear here.")
        main_layout.addWidget(output_label)
        main_layout.addWidget(self.output_text_area, 1)

    def init_worker_thread(self):
        """ Initializes the QThread and Worker object. """
        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)
        self.request_process_url.connect(self.worker.process_url)
        self.worker.finished.connect(self.on_processing_finished)
        self.worker.error.connect(self.on_processing_error)
        # --- FIX: Connect the thread's finished signal to clean up the worker ---
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.start()

    def handle_button_click(self):
        """ Manages the state of the application based on button clicks. """
        if not self.is_running:
            all_urls = self.url_input_area.toPlainText().strip().splitlines()
            self.urls_to_process = [url.strip() for url in all_urls if url.strip()]

            if not self.urls_to_process:
                QMessageBox.warning(self, "No URLs", "Please enter at least one valid URL.")
                return
            
            self.is_running = True
            self.current_url_index = 0
            
            self.process_button.setText(f"Process Next URL (1/{len(self.urls_to_process)})")
            self.url_input_area.setDisabled(True)
            self.mode_combo.setDisabled(True)
            self.input_stack.setDisabled(True)
            self.progress_bar.setMaximum(len(self.urls_to_process))
            self.progress_bar.setValue(0)
            self.output_text_area.clear()
            
            self.process_next_url()
        else:
            self.current_url_index += 1
            self.process_next_url()
            
    def process_next_url(self):
        """ Checks if there are more URLs to process and triggers the worker. """
        if self.current_url_index < len(self.urls_to_process):
            url = self.urls_to_process[self.current_url_index]
            user_input = ""
            
            mode_index = self.mode_combo.currentIndex()
            if self.current_url_index == 0:
                if mode_index == 0:
                    user_input = self.keyword_input.text().strip()
                else:
                    self.target_tag_name = self.tag_input.text().strip().lower()

            self.process_button.setDisabled(True)
            self.output_text_area.setText(f"Requesting and parsing {url}...")
            self.request_process_url.emit(url, user_input, self.target_tag_name)
        else:
            self.reset_state()

    @pyqtSlot(str, str)
    def on_processing_finished(self, text_content, discovered_tag):
        if discovered_tag and not self.target_tag_name:
            self.target_tag_name = discovered_tag
        self.output_text_area.setText(text_content)
        self.update_ui_after_task()

    @pyqtSlot(str)
    def on_processing_error(self, error_message):
        self.output_text_area.setText(error_message)
        self.update_ui_after_task()

    def update_ui_after_task(self):
        self.progress_bar.setValue(self.current_url_index + 1)
        
        if self.current_url_index >= len(self.urls_to_process) - 1:
            self.output_text_area.append("\n\n--- All URLs processed. ---")
            self.process_button.hide()
            self.reset_button.show()
        else:
            self.process_button.setEnabled(True)
            next_num = self.current_url_index + 2
            total = len(self.urls_to_process)
            self.process_button.setText(f"Process Next URL ({next_num}/{total})")

    def reset_state(self):
        """ Resets the UI and internal state, ready for new input. """
        self.is_running = False
        self.urls_to_process = []
        self.current_url_index = -1
        self.target_tag_name = ""
        
        self.reset_button.hide()
        self.process_button.setText("Start Processing")
        self.process_button.show()
        self.process_button.setEnabled(True)

        self.url_input_area.setEnabled(True)
        self.mode_combo.setEnabled(True)
        self.input_stack.setEnabled(True)
        self.progress_bar.setValue(0)
        self.output_text_area.clear()
        self.output_text_area.setPlaceholderText("Text from the processed webpage will appear here.")

    def stop_thread(self):
        """A dedicated method to safely stop the thread."""
        if self.thread and self.thread.isRunning():
            self.thread.quit()  # Tells the thread's event loop to exit
            self.thread.wait()  # Waits for the thread to finish executing



    def closeEvent(self, event):
        """Ensures the thread is stopped when the widget is closed."""
        self.stop_thread()
        super().closeEvent(event)

# This class needs to be defined for the main application to run, even if it's not the focus.
class SellerFollowupTab(QWidget):
     def reset_process(self):
         # A dummy method to prevent errors when the main window calls it on close.
         pass

# --- Main Application Execution ---
# This part is included so the file can be run standalone for testing.
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLESHEET)
    
    main_window = QMainWindow()
    main_window.setWindowTitle("HTML to Text Converter")
    main_window.setGeometry(300, 300, 700, 800)

    central_widget = HtmlToTextTab()
    # --- FIX: Ensure the main window's closeEvent triggers the widget's closeEvent ---
    main_window.setCentralWidget(central_widget)
    
    main_window.show()
    sys.exit(app.exec_())
