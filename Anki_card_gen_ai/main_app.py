# AnkiConnect_AI_Generator/main_app.py
import sys
import json
import os
from pathlib import Path
import time # For potential small delays if needed

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QComboBox, QMessageBox, QDialog, QProgressDialog,
    QAbstractItemView
)
from PyQt6.QtCore import Qt, QTimer # No QThread, QObject, pyqtSignal needed from QtCore for workers

# Import our local modules
from .consts import (
    DEFAULT_GEMINI_MODEL, BASE_LLM_PROMPT,
    COL_SELECT, COL_TYPE, COL_FRONT, COL_BACK, COL_TAGS,
    CONFIG_FILE_NAME
)
from .anki_connect_client import AnkiConnectClient
from .gemini_client import GeminiFlashcardGenerator

# --- Configuration Handling (same as before) ---
def get_app_config_path() -> Path:
    app_data_dir = Path(os.getenv("APPDATA") or os.getenv("LOCALAPPDATA") or Path.home() / ".config")
    app_specific_dir = app_data_dir / "AI_Flashcard_Generator_AnkiConnect"
    app_specific_dir.mkdir(parents=True, exist_ok=True)
    return app_specific_dir / CONFIG_FILE_NAME

def load_config() -> dict:
    config_path = get_app_config_path()
    default_config = {
        "gemini_api_key": "",
        "gemini_model": DEFAULT_GEMINI_MODEL,
        "last_deck_name": "AI Generated Cards",
        "custom_system_instructions": ""
    }
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except json.JSONDecodeError:
            return default_config
    return default_config

def save_config(config: dict) -> None:
    config_path = get_app_config_path()
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except IOError as e:
        print(f"Error saving config: {e}")

# --- Main Application Window ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Flashcard Generator (Synchronous)")
        self.setMinimumSize(850, 750)

        self.config = load_config()
        self.anki_client = AnkiConnectClient()
        # Gemini client will be created on demand or once if API key is present
        self.gemini_generator = None # Will be initialized in on_generate_clicked
        self.generated_cards_data = []
        
        self.is_busy = False # Simple flag to prevent overlapping blocking operations

        self._init_ui()
        self._load_config_into_ui()
        self._connect_signals()
        self.update_all_button_states() # Initial button states
        
        QTimer.singleShot(100, self.check_ankiconnect_connection_blocking)

    def _init_ui(self):
        # ... (UI setup same as your last full script) ...
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        api_key_layout = QHBoxLayout()
        api_key_layout.addWidget(QLabel("Gemini API Key:"))
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        api_key_layout.addWidget(self.api_key_edit)
        main_layout.addLayout(api_key_layout)
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Gemini Model:"))
        self.model_edit = QLineEdit()
        model_layout.addWidget(self.model_edit)
        main_layout.addLayout(model_layout)
        main_layout.addWidget(QLabel("Paragraph / Lesson Content:"))
        self.paragraph_edit = QTextEdit()
        self.paragraph_edit.setPlaceholderText("Paste your lesson content here...")
        self.paragraph_edit.setFixedHeight(150)
        main_layout.addWidget(self.paragraph_edit)
        deck_layout = QHBoxLayout()
        deck_layout.addWidget(QLabel("Anki Deck Name:"))
        self.deck_combo = QComboBox()
        self.deck_combo.setEditable(True)
        deck_layout.addWidget(self.deck_combo)
        self.refresh_decks_button = QPushButton("Refresh Decks")
        deck_layout.addWidget(self.refresh_decks_button)
        main_layout.addLayout(deck_layout)
        main_layout.addWidget(QLabel("Custom System Instructions (Optional):"))
        self.custom_instructions_edit = QTextEdit()
        self.custom_instructions_edit.setPlaceholderText("e.g., Focus on definitions. Generate exactly 5 cards.")
        self.custom_instructions_edit.setFixedHeight(80)
        main_layout.addWidget(self.custom_instructions_edit)
        self.generate_button = QPushButton("Generate Flashcards")
        self.generate_button.setFixedHeight(40)
        main_layout.addWidget(self.generate_button)
        main_layout.addWidget(QLabel("Generated Flashcards:"))
        self.cards_table = QTableWidget()
        self.cards_table.setColumnCount(5)
        self.cards_table.setHorizontalHeaderLabels(["Select", "Type", "Front", "Back", "Tags"])
        self.cards_table.horizontalHeader().setSectionResizeMode(COL_FRONT, QHeaderView.ResizeMode.Stretch)
        self.cards_table.horizontalHeader().setSectionResizeMode(COL_BACK, QHeaderView.ResizeMode.Stretch)
        self.cards_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.cards_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.cards_table.setColumnWidth(COL_SELECT, 50)
        self.cards_table.setColumnWidth(COL_TYPE, 80)
        self.cards_table.setColumnWidth(COL_TAGS, 120)
        main_layout.addWidget(self.cards_table)
        self.select_all_checkbox = QCheckBox("Select All / Deselect All")
        main_layout.addWidget(self.select_all_checkbox)
        self.import_button = QPushButton("Import Selected Cards to Anki")
        self.import_button.setFixedHeight(40)
        main_layout.addWidget(self.import_button)
        self.status_label = QLabel("Ready.")
        main_layout.addWidget(self.status_label)

    def _load_config_into_ui(self):
        self.api_key_edit.setText(self.config.get("gemini_api_key", ""))
        self.model_edit.setText(self.config.get("gemini_model", DEFAULT_GEMINI_MODEL))
        self.deck_combo.setCurrentText(self.config.get("last_deck_name", "AI Generated Cards"))
        self.custom_instructions_edit.setPlainText(self.config.get("custom_system_instructions", ""))

    def _save_ui_to_config(self):
        self.config["gemini_api_key"] = self.api_key_edit.text()
        self.config["gemini_model"] = self.model_edit.text()
        self.config["last_deck_name"] = self.deck_combo.currentText()
        self.config["custom_system_instructions"] = self.custom_instructions_edit.toPlainText()
        save_config(self.config)

    def _connect_signals(self):
        self.generate_button.clicked.connect(self.on_generate_clicked_blocking) # Now blocking
        self.import_button.clicked.connect(self.on_import_clicked_blocking)
        self.refresh_decks_button.clicked.connect(self.fetch_deck_names_blocking)
        self.select_all_checkbox.stateChanged.connect(self.on_select_all_changed)
        self.cards_table.itemChanged.connect(self.on_table_item_changed)

    def set_busy_state(self, busy: bool, message: str = "Processing..."):
        self.is_busy = busy
        if busy:
            self.status_label.setText(f"Status: {message}")
        else:
            self.status_label.setText("Status: Ready.") # Or a more specific ready message
        self.update_all_button_states()
        QApplication.processEvents() # Allow UI to update

    def update_all_button_states(self):
        # Enable buttons only if not busy
        self.generate_button.setEnabled(not self.is_busy)
        self.refresh_decks_button.setEnabled(not self.is_busy)
        
        # Import button specific logic
        selected_count = 0
        if self.cards_table.rowCount() > 0:
            for i in range(self.cards_table.rowCount()):
                item = self.cards_table.item(i, COL_SELECT)
                if item and item.checkState() == Qt.CheckState.Checked:
                    selected_count += 1
        
        self.import_button.setEnabled(selected_count > 0 and not self.is_busy)
        if selected_count > 0:
            self.import_button.setText(f"Import {selected_count} Selected Card(s) to Anki")
        else:
            self.import_button.setText("Import Selected Cards to Anki")


    # --- AnkiConnect Methods (Blocking) ---
    def check_ankiconnect_connection_blocking(self):
        if self.is_busy: return
        self.set_busy_state(True, "Checking AnkiConnect...")
        print("[MainWindow] check_ankiconnect_connection_blocking called")
        try:
            result = self.anki_client.request_permission()
            print(f"[MainWindow] AnkiConnect permission result: {result}")
            if isinstance(result, str) or not isinstance(result, dict) or result.get("permission") != "granted":
                error_msg = result if isinstance(result, str) else result.get("error", "Permission denied/unexpected.")
                QMessageBox.warning(self, "AnkiConnect Error", f"Details: {error_msg}")
                self.set_busy_state(False) # Reset busy state
                self.status_label.setText(f"Status: AnkiConnect Error - {error_msg}") # Keep error message
            else:
                self.set_busy_state(False) # No longer busy with this specific task
                self.fetch_deck_names_blocking() # Chain to next blocking call
        except Exception as e:
            print(f"[MainWindow] Exception in check_ankiconnect_connection_blocking: {e}")
            QMessageBox.warning(self, "AnkiConnect Error", f"Connection failed: {e}")
            self.set_busy_state(False)
            self.status_label.setText(f"Status: AnkiConnect Connection failed - {e}")

    def fetch_deck_names_blocking(self):
        if self.is_busy: return
        self.set_busy_state(True, "Fetching deck names...")
        print("[MainWindow] fetch_deck_names_blocking called")
        try:
            result = self.anki_client.get_deck_names()
            print(f"[MainWindow] fetch_deck_names_blocking result: {result}")
            if isinstance(result, list):
                current_deck = self.deck_combo.currentText()
                self.deck_combo.blockSignals(True)
                self.deck_combo.clear(); self.deck_combo.addItems(sorted(result))
                if current_deck in result: self.deck_combo.setCurrentText(current_deck)
                elif result: self.deck_combo.setCurrentIndex(0)
                else: self.deck_combo.setCurrentText(current_deck or self.config.get("last_deck_name", "AI Generated"))
                self.deck_combo.blockSignals(False)
                self.status_label.setText(f"Status: AnkiConnect ready. {len(result)} decks loaded.") # Keep specific status
            else:
                QMessageBox.warning(self, "AnkiConnect Error", f"Could not fetch deck names: {result}")
                self.status_label.setText(f"Status: Error fetching decks - {result}")
        except Exception as e:
            print(f"[MainWindow] Exception in fetch_deck_names_blocking: {e}")
            QMessageBox.warning(self, "AnkiConnect Error", f"Could not fetch deck names: {e}")
            self.status_label.setText(f"Status: Error fetching decks - {e}")
        finally:
            self.set_busy_state(False) # Reset busy after this task

    def on_import_clicked_blocking(self):
        if self.is_busy: return
        print("[MainWindow] on_import_clicked_blocking called")
        selected_card_objects = []
        for i in range(self.cards_table.rowCount()):
            item = self.cards_table.item(i, COL_SELECT)
            if item and item.checkState() == Qt.CheckState.Checked:
                card_data = item.data(Qt.ItemDataRole.UserRole)
                if card_data: selected_card_objects.append(card_data)
        if not selected_card_objects: QMessageBox.warning(self, "Input Error", "No cards selected."); return
        deck_name = self.deck_combo.currentText().strip()
        if not deck_name: QMessageBox.warning(self, "Input Error", "Please specify deck name."); return
        
        self._save_ui_to_config()
        reply = QMessageBox.question(self, "Confirm Import", f"Import {len(selected_card_objects)} cards?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No: return

        self.set_busy_state(True, f"Importing {len(selected_card_objects)} cards...")
        self.generate_button.setText("Generate Flashcards") # Reset text for other buttons too

        notes_to_add_anki_format = []
        for card_obj in selected_card_objects:
            fields = {}
            if card_obj['cardType'] == "Basic":
                fields["Front"], fields["Back"] = card_obj['front'], card_obj['back']
            elif card_obj['cardType'] == "Cloze":
                fields["Text"] = card_obj['front']
            else: continue
            notes_to_add_anki_format.append({
                "deckName": deck_name, "modelName": card_obj['cardType'],
                "fields": fields, 
                "tags": card_obj.get('tags', "").split()
            })
        
        try:
            result = self.anki_client.add_notes(notes_to_add_anki_format)
            print(f"[MainWindow] on_import_clicked_blocking result: {result}")
            if isinstance(result, list):
                successful_imports = sum(1 for item in result if item is not None)
                errors = len(result) - successful_imports
                msg = f"{successful_imports} imported." + (f" {errors} failed." if errors > 0 else "")
                QMessageBox.information(self, "Import Complete", msg)
                self.status_label.setText(f"Status: {msg}")
                self.cards_table.setRowCount(0); self.generated_cards_data = []; self.select_all_checkbox.setChecked(False)
            else:
                QMessageBox.critical(self, "AnkiConnect Import Error", f"Failed: {result}")
                self.status_label.setText(f"Status: Import Error - {result}")
        except Exception as e:
            print(f"[MainWindow] Exception in on_import_clicked_blocking: {e}")
            QMessageBox.critical(self, "AnkiConnect Import Error", f"Failed: {e}")
            self.status_label.setText(f"Status: Import Error - {e}")
        finally:
            self.set_busy_state(False)

    # --- Gemini Methods (Now also Blocking) ---
    def on_generate_clicked_blocking(self):
        if self.is_busy: return
        api_key = self.api_key_edit.text().strip()
        model_name = self.model_edit.text().strip()
        paragraph = self.paragraph_edit.toPlainText().strip()
        if not api_key: QMessageBox.warning(self, "Input Error", "API Key missing."); return
        if not model_name: QMessageBox.warning(self, "Input Error", "Model name missing."); return
        if not paragraph: QMessageBox.warning(self, "Input Error", "Paragraph missing."); return

        self._save_ui_to_config()
        self.set_busy_state(True, "Generating flashcards with Gemini...")
        self.cards_table.setRowCount(0); self.generated_cards_data = []
        self.import_button.setText("Import Selected Cards to Anki") # Reset import button text
        
        full_prompt = f"{self.custom_instructions_edit.toPlainText().strip()}\n\n{BASE_LLM_PROMPT}\n\nParagraph:\n{paragraph}"
        
        try:
            print(f"[MainWindow] Initializing GeminiFlashcardGenerator with key: ...{api_key[-4:]} model: {model_name}")
            # Create a new generator instance each time or reuse if API key/model doesn't change often
            # For simplicity, creating new one here.
            self.gemini_generator = GeminiFlashcardGenerator(api_key=api_key, model_name=model_name)
            
            print("[MainWindow] Calling generate_cards_from_text (BLOCKING)...")
            result = self.gemini_generator.generate_cards_from_text(full_prompt) # BLOCKING CALL
            print(f"[MainWindow] Gemini generate_cards_from_text result type: {type(result)}")

            if isinstance(result, str): # Error from Gemini (should be caught by its internal try-except)
                QMessageBox.critical(self, "Gemini API Error", result)
                self.status_label.setText(f"Status: Error - {result}")
            elif not result: # Empty list or None
                QMessageBox.information(self, "No Cards", "Gemini did not return any cards.")
                self.status_label.setText("Status: No cards generated by Gemini.")
            else: # Success
                self.generated_cards_data = result
                self._populate_cards_table(result)
                self.status_label.setText(f"Status: {len(result)} cards generated. Review and select for import.")
        except Exception as e:
            print(f"[MainWindow] Exception in on_generate_clicked_blocking: {e}")
            QMessageBox.critical(self, "Gemini API Error", str(e))
            self.status_label.setText(f"Status: Gemini Error - {e}")
        finally:
            self.set_busy_state(False)
            self.generate_button.setText("Generate Flashcards") # Reset button text if it was changed


    # --- Common UI Update Methods (mostly same) ---
    def _populate_cards_table(self, cards_data: list):
        self.cards_table.setRowCount(0); self.cards_table.blockSignals(True)
        for i, card in enumerate(cards_data):
            self.cards_table.insertRow(i)
            chk_box_item = QTableWidgetItem()
            chk_box_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            chk_box_item.setCheckState(Qt.CheckState.Checked)
            chk_box_item.setData(Qt.ItemDataRole.UserRole, card)
            self.cards_table.setItem(i, COL_SELECT, chk_box_item)
            self.cards_table.setItem(i, COL_TYPE, QTableWidgetItem(card.get("cardType", "N/A")))
            self.cards_table.setItem(i, COL_FRONT, QTableWidgetItem(card.get("front", "")))
            self.cards_table.setItem(i, COL_BACK, QTableWidgetItem(card.get("back", "")))
            self.cards_table.setItem(i, COL_TAGS, QTableWidgetItem(card.get("tags", "")))
        self.cards_table.blockSignals(False); self.cards_table.resizeRowsToContents()
        self.select_all_checkbox.setChecked(True); self.update_all_button_states()

    def on_select_all_changed(self, state):
        self.cards_table.blockSignals(True)
        check_state = Qt.CheckState(state)
        for i in range(self.cards_table.rowCount()):
            item = self.cards_table.item(i, COL_SELECT)
            if item: item.setCheckState(check_state)
        self.cards_table.blockSignals(False); self.update_all_button_states()

    def on_table_item_changed(self, item: QTableWidgetItem):
        if item.column() == COL_SELECT:
            self.update_all_button_states()
            all_checked, none_checked = True, True
            if self.cards_table.rowCount() == 0: all_checked, none_checked = False, True
            else:
                for i in range(self.cards_table.rowCount()):
                    cb_item = self.cards_table.item(i, COL_SELECT)
                    if cb_item and cb_item.checkState() == Qt.CheckState.Checked: none_checked = False
                    elif cb_item and cb_item.checkState() == Qt.CheckState.Unchecked: all_checked = False
            self.select_all_checkbox.blockSignals(True)
            if all_checked and self.cards_table.rowCount() > 0: self.select_all_checkbox.setCheckState(Qt.CheckState.Checked)
            elif none_checked or self.cards_table.rowCount() == 0: self.select_all_checkbox.setCheckState(Qt.CheckState.Unchecked)
            else: self.select_all_checkbox.setCheckState(Qt.CheckState.PartiallyChecked)
            self.select_all_checkbox.blockSignals(False)

    def closeEvent(self, event):
        self._save_ui_to_config()
        # No threads to explicitly manage here other than Qt's own event loop
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())