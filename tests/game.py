import sys
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox
)
from PyQt5.QtCore import Qt


class PokemonGuessingGame(QWidget):
    def __init__(self, json_path):
        super().__init__()
        self.setWindowTitle("Juego de Adivinanza Pokémon")
        self.pokemons = self.load_pokemons(json_path)
        self.current_index = 0
        self.current_clue_index = 0
        self.init_ui()

    def load_pokemons(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el archivo JSON:\n{e}")
            return []

    def init_ui(self):
        self.setFixedSize(450, 280)
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            QLabel#title {
                font-size: 22px;
                font-weight: bold;
                color: #ffcb05;
                text-align: center;
                margin-bottom: 15px;
            }
            QLabel#clueLabel {
                font-size: 18px;
                color: #2a75bb;
                margin-bottom: 20px;
                min-height: 60px;
            }
            QLineEdit {
                font-size: 16px;
                padding: 6px;
                border: 2px solid #2a75bb;
                border-radius: 8px;
            }
            QPushButton {
                background-color: #2a75bb;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #1a4f8b;
            }
            QLabel#feedback {
                font-size: 16px;
                margin-top: 15px;
                min-height: 30px;
            }
        """)

        layout = QVBoxLayout()

        self.title_label = QLabel("Adivina el Pokémon")
        self.title_label.setObjectName("title")
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)

        self.clue_label = QLabel("")
        self.clue_label.setObjectName("clueLabel")
        self.clue_label.setWordWrap(True)
        self.clue_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.clue_label)

        input_layout = QHBoxLayout()
        self.input_guess = QLineEdit()
        self.input_guess.setPlaceholderText("Escribe aquí tu respuesta")
        self.input_guess.returnPressed.connect(self.check_guess)
        input_layout.addWidget(self.input_guess)

        self.next_clue_button = QPushButton("Siguiente pista")
        self.next_clue_button.clicked.connect(self.next_clue)
        input_layout.addWidget(self.next_clue_button)

        layout.addLayout(input_layout)

        self.feedback_label = QLabel("")
        self.feedback_label.setObjectName("feedback")
        self.feedback_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.feedback_label)

        nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("Anterior Pokémon")
        self.prev_button.clicked.connect(self.prev_pokemon)
        nav_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("Siguiente Pokémon")
        self.next_button.clicked.connect(self.next_pokemon)
        nav_layout.addWidget(self.next_button)

        layout.addLayout(nav_layout)

        self.setLayout(layout)
        self.show_current_pokemon()

    def show_current_pokemon(self):
        if not self.pokemons:
            self.clue_label.setText("No hay Pokémon para adivinar.")
            self.input_guess.setEnabled(False)
            self.next_clue_button.setEnabled(False)
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
            return

        self.current_clue_index = 0
        self.input_guess.clear()
        self.feedback_label.clear()
        self.input_guess.setEnabled(True)
        self.next_clue_button.setEnabled(True)
        self.prev_button.setEnabled(True)
        self.next_button.setEnabled(True)

        self.show_clue()

    def show_clue(self):
        clues = self.pokemons[self.current_index]["clues"]
        if self.current_clue_index < len(clues):
            self.clue_label.setText(f"Pista {self.current_clue_index + 1} de {len(clues)}:\n\n{clues[self.current_clue_index]}")
        else:
            self.clue_label.setText("No hay más pistas para este Pokémon.")

    def next_clue(self):
        clues = self.pokemons[self.current_index]["clues"]
        if self.current_clue_index + 1 < len(clues):
            self.current_clue_index += 1
            self.show_clue()
        else:
            self.feedback_label.setText("No hay más pistas.")
            self.feedback_label.setStyleSheet("color: orange; font-weight: bold;")

    def check_guess(self):
        guess = self.input_guess.text().strip().lower()
        correct_name = self.pokemons[self.current_index]["name"].lower()

        if not guess:
            self.feedback_label.setText("Por favor, ingresa una respuesta.")
            self.feedback_label.setStyleSheet("color: orange;")
            return

        if guess == correct_name:
            self.feedback_label.setText(f"🎉 ¡Correcto! Es {self.pokemons[self.current_index]['name']}.")
            self.feedback_label.setStyleSheet("color: green; font-weight: bold;")
            self.input_guess.setEnabled(False)
            self.next_clue_button.setEnabled(False)
        else:
            self.feedback_label.setText("❌ Incorrecto, intenta otra vez.")
            self.feedback_label.setStyleSheet("color: red;")

    def next_pokemon(self):
        if not self.pokemons:
            return
        self.current_index = (self.current_index + 1) % len(self.pokemons)
        self.show_current_pokemon()

    def prev_pokemon(self):
        if not self.pokemons:
            return
        self.current_index = (self.current_index - 1) % len(self.pokemons)
        self.show_current_pokemon()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    game = PokemonGuessingGame("pokemons.json")
    game.resize(450, 280)
    game.show()
    sys.exit(app.exec())
