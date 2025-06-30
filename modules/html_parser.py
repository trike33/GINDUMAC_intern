import sys
import requests
import re
from bs4 import BeautifulSoup, NavigableString
from urllib.parse import urljoin, urlencode

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QProgressBar, QLabel, QMainWindow, QMessageBox,
    QLineEdit, QComboBox, QStackedWidget
)
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot

# (Stylesheet remains the same)
DARK_STYLESHEET = """
QWidget {
    font-family: 'Segoe UI', Arial, sans-serif; font-size: 14px;
    background-color: #2c3e50; color: #ecf0f1;
}
QLabel { font-weight: bold; color: #1abc9c; padding-bottom: 5px; }
QTextEdit, QLineEdit, QComboBox {
    background-color: #34495e; border: 1px solid #4a627a;
    border-radius: 5px; padding: 8px; color: #ecf0f1;
}
QPushButton {
    background-color: #1abc9c; color: white; border: none;
    padding: 10px 15px; border-radius: 5px; font-weight: bold;
}
QPushButton:hover { background-color: #16a085; }
QPushButton:disabled { background-color: #95a5a6; }
QProgressBar {
    border: 1px solid #4a627a; border-radius: 5px; text-align: center;
    background-color: #34495e; color: #ecf0f1;
}
QProgressBar::chunk { background-color: #1abc9c; border-radius: 4px; }
"""

class Worker(QObject):
    """ Performs network requests and parsing in a separate thread. """
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    @pyqtSlot(str, str, int)
    def process_url(self, url, user_input, mode_index):
        """
        Fetches a URL and performs contextual text and link extraction.
        """
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            body = soup.find('body')

            if not body:
                self.error.emit(f"Could not find a <body> tag in {url}.")
                return

            if mode_index == 2:
                self.finished.emit(body.get_text(separator='\n', strip=True))
                return

            primary_tags = []
            if mode_index == 0: # Find by Keyword
                if not user_input:
                    self.error.emit("Please provide a keyword for this mode.")
                    return
                # --- MODIFIED: Search in text and attributes for keyword ---
                # 1. Find in text nodes
                text_nodes = body.find_all(string=lambda text: isinstance(text, NavigableString) and user_input.lower() in text.lower())
                tags_from_text = [node.parent for node in text_nodes]
                # 2. Find in attributes
                def attr_filter(tag):
                    if tag.name in ['script', 'style']: return False
                    for attr_val in tag.attrs.values():
                        if isinstance(attr_val, str) and user_input.lower() in attr_val.lower(): return True
                        if isinstance(attr_val, list) and any(user_input.lower() in str(item).lower() for item in attr_val): return True
                    return False
                tags_from_attrs = body.find_all(attr_filter)
                # 3. Combine and get unique tags
                primary_tags = list(set(tags_from_text + tags_from_attrs))
            
            elif mode_index == 1: # Find by Tag Name
                if not user_input:
                    self.error.emit("Please provide an HTML tag (e.g., h3, div) for this mode.")
                    return
                primary_tags = body.find_all(user_input)
            
            if not primary_tags:
                self.finished.emit(f"No matching content found for '{user_input}' in {url}.")
                return

            output_lines = []
            for tag in primary_tags:
                tag_text = tag.get_text(strip=True).replace('\n', ' ').strip()
                if not tag_text: continue

                # --- REWRITTEN: More robust search for a nearby link or form ---
                link_url = "[No link found nearby]"
                found = False
                
                # Strategy 1: Check if the tag itself is a link.
                if tag.name == 'a' and tag.has_attr('href'):
                    link_url = urljoin(response.url, tag['href'])
                    found = True

                # Strategy 2: Look UP. Is the tag's parent a link?
                if not found:
                    parent_link = tag.find_parent('a', href=True)
                    if parent_link:
                        link_url = urljoin(response.url, parent_link['href'])
                        found = True
                
                # Strategy 3: Look DOWN. Is there a link inside the primary tag?
                if not found:
                    inner_link = tag.find('a', href=True)
                    if inner_link:
                        link_url = urljoin(response.url, inner_link['href'])
                        found = True

                # Strategy 4: Look SIDEWAYS. Is there a link in the next few siblings?
                if not found:
                    for sibling in tag.find_next_siblings(limit=5):
                        elements_to_check = [sibling] + sibling.find_all(['a', 'form'])
                        for element in elements_to_check:
                            if element.name == 'a' and element.has_attr('href'):
                                link_url = urljoin(response.url, element['href'])
                                found = True
                                break
                            if element.name == 'form' and element.get('method', 'get').lower() == 'get' and element.has_attr('action'):
                                base_action_url = urljoin(response.url, element['action'])
                                params = {inp['name']: inp['value'] for inp in element.find_all('input', {'name': True, 'value': True})}
                                query_string = urlencode(params)
                                link_url = f"{base_action_url}?{query_string}" if query_string else base_action_url
                                found = True
                                break
                        if found:
                            break

                output_lines.append(f"{tag_text} -> {link_url}")
            
            self.finished.emit("\n".join(output_lines))

        except requests.exceptions.RequestException as e:
            self.error.emit(f"Network Error for {url}:\n{str(e)}")
        except Exception as e:
            self.error.emit(f"An unexpected error occurred for {url}:\n{str(e)}")


class HtmlToTextTab(QWidget):
    """ Main widget for the HTML parsing functionality. """
    request_process_url = pyqtSignal(str, str, int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_running = False
        self.init_ui()
        self.init_worker_thread()

    def init_ui(self):
        """ Sets up the user interface. """
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)

        main_layout.addWidget(QLabel("Enter URLs (one per line):"))
        self.url_input_area = QTextEdit()
        main_layout.addWidget(self.url_input_area)

        main_layout.addWidget(QLabel("Select Extraction Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "Find by Keyword (Get Text & Link)", 
            "Specify HTML Tag (Get Text & Link)", 
            "Extract Body Text Only"
        ])
        
        self.input_stack = QStackedWidget()
        self.keyword_input = QLineEdit("Enter keyword...")
        self.tag_input = QLineEdit("h3")
        self.input_stack.addWidget(self.keyword_input)
        self.input_stack.addWidget(self.tag_input)
        self.input_stack.addWidget(QWidget())
        self.mode_combo.currentIndexChanged.connect(self.input_stack.setCurrentIndex)
        
        main_layout.addWidget(self.mode_combo)
        main_layout.addWidget(self.input_stack)

        controls_layout = QHBoxLayout()
        self.process_button = QPushButton("Start Processing")
        self.process_button.clicked.connect(self.handle_button_click)
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_state)
        self.reset_button.hide()
        self.progress_bar = QProgressBar()
        controls_layout.addWidget(self.process_button)
        controls_layout.addWidget(self.reset_button)
        controls_layout.addWidget(self.progress_bar)
        main_layout.addLayout(controls_layout)

        main_layout.addWidget(QLabel("Output:"))
        self.output_text_area = QTextEdit()
        self.output_text_area.setReadOnly(True)
        main_layout.addWidget(self.output_text_area, 1)

    def init_worker_thread(self):
        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)
        self.request_process_url.connect(self.worker.process_url)
        self.worker.finished.connect(self.on_processing_finished)
        self.worker.error.connect(self.on_processing_error)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.start()

    def handle_button_click(self):
        if not self.is_running:
            self.urls_to_process = [url.strip() for url in self.url_input_area.toPlainText().strip().splitlines() if url.strip()]
            if not self.urls_to_process:
                QMessageBox.warning(self, "No URLs", "Please enter at least one valid URL.")
                return
            
            self.is_running = True
            self.current_url_index = 0
            for w in [self.url_input_area, self.mode_combo, self.input_stack]: w.setDisabled(True)
            self.progress_bar.setMaximum(len(self.urls_to_process))
            self.output_text_area.clear()
            self.process_next_url()
        else:
            self.current_url_index += 1
            self.process_next_url()
            
    def process_next_url(self):
        if self.current_url_index < len(self.urls_to_process):
            url = self.urls_to_process[self.current_url_index]
            mode_index = self.mode_combo.currentIndex()
            user_input = ""
            if mode_index == 0: user_input = self.keyword_input.text().strip()
            elif mode_index == 1: user_input = self.tag_input.text().strip().lower()
            
            self.process_button.setDisabled(True)
            self.output_text_area.setText(f"Requesting and parsing {url}...")
            self.request_process_url.emit(url, user_input, mode_index)

    @pyqtSlot(str)
    def on_processing_finished(self, result_text):
        self.output_text_area.setText(result_text)
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
            next_num, total = self.current_url_index + 2, len(self.urls_to_process)
            self.process_button.setText(f"Process Next URL ({next_num}/{total})")

    def reset_state(self):
        self.is_running = False
        self.urls_to_process = []
        self.current_url_index = -1
        self.reset_button.hide()
        self.process_button.show()
        self.process_button.setEnabled(True)
        self.process_button.setText("Start Processing")
        for w in [self.url_input_area, self.mode_combo, self.input_stack]: w.setEnabled(True)
        self.progress_bar.setValue(0)
        self.output_text_area.clear()

    def reset_process(self):
        """
        A dedicated method to safely stop the worker thread.
        This is called by the main window's closeEvent.
        """
        print("Attempting to stop thread for HtmlToTextTab...")
        if hasattr(self, 'thread') and self.thread.isRunning():
            self.thread.quit()
            # Wait for 3 seconds for a graceful shutdown
            if not self.thread.wait(3000):
                print("HtmlToTextTab thread is unresponsive, terminating it.")
                self.thread.terminate() # Force termination
                self.thread.wait() # Wait for termination to complete
            print("HtmlToTextTab thread stopped.")