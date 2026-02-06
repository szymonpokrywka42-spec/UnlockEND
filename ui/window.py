import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QPushButton, 
                             QLabel, QFileDialog, QMessageBox, QInputDialog, 
                             QLineEdit, QSystemTrayIcon, QMenu, QProgressDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QShortcut, QKeySequence, QGuiApplication, QIcon
from ui.menu import AppMenu
from ui.console import DebugConsoleWidget
from ui.drop_handler import DropHandler
from core.engine import UnlockWorker

class MainWindow(QMainWindow):
    def __init__(self, engine, logger):
        super().__init__()
        self.pending_path = None
        self.engine = engine
        self.logger = logger
        self.current_token = ""
        self.tray_icon = None
        
        self.init_ui()
        self.init_tray()
        
        self.setAcceptDrops(True)
        self.drop_handler = DropHandler(self)
        
        self.logger.set_callback(self.console_widget.append_log)
        self.console_widget.command_submitted.connect(self.handle_console_command)
        
        self.console_shortcut = QShortcut(QKeySequence("F12"), self)
        self.console_shortcut.activated.connect(self.toggle_console)

    def init_ui(self):
        self.setWindowTitle("UnlockEND")
        self.setMinimumSize(500, 500)

        self.menu_bar = AppMenu(self)
        self.setMenuBar(self.menu_bar)
        self.menu_bar.connect_actions(self)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setSpacing(15)
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        self.status_label = QLabel("Ready to Secure")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        token_container = QWidget()
        token_sub_layout = QVBoxLayout(token_container)
        
        self.token_display = QLabel("TOKEN: ********")
        self.token_display.setObjectName("tokenDisplay")
        self.token_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.token_display.setStyleSheet("font-family: monospace; font-size: 14px; font-weight: bold;")
        
        self.copy_btn = QPushButton("📋 COPY TOKEN")
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.setEnabled(False)
        self.copy_btn.setFixedWidth(180)
        self.copy_btn.clicked.connect(self.copy_token_to_clipboard)
        
        token_sub_layout.addWidget(self.token_display)
        token_sub_layout.addWidget(self.copy_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.lock_button = QPushButton("LOCK")
        self.lock_button.setObjectName("lockButton")
        self.lock_button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.unlock_button = QPushButton("UNLOCK")
        self.unlock_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.main_layout.addWidget(self.status_label)
        self.main_layout.addStretch()
        self.main_layout.addWidget(token_container)
        self.main_layout.addStretch()
        self.main_layout.addWidget(self.lock_button)
        self.main_layout.addWidget(self.unlock_button)

        self.console_widget = DebugConsoleWidget()
        self.console_widget.setVisible(False)
        self.main_layout.addWidget(self.console_widget)

        self.lock_button.clicked.connect(self.handle_lock)
        self.unlock_button.clicked.connect(self.handle_unlock)

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon.fromTheme("security-high", QIcon.fromTheme("lock")))
        
        tray_menu = QMenu()
        show_action = tray_menu.addAction("Show Window")
        show_action.triggered.connect(self.showNormal)
        tray_menu.addSeparator()
        exit_action = tray_menu.addAction("Exit Completely")
        exit_action.triggered.connect(self.quit_application)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

    def start_operation_worker(self, mode, path, token=None):
        self.progress_dialog = QProgressDialog("Initializing...", "Cancel", 0, 100, self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setWindowTitle("UnlockEND Task")
        self.progress_dialog.show()

        self.worker = UnlockWorker(self.engine, mode, path, token)
        self.worker.status_sig.connect(self.progress_dialog.setLabelText)
        self.worker.progress_sig.connect(self.progress_dialog.setValue)
        self.worker.finished_sig.connect(self.on_operation_finished)
        self.worker.finished_sig.connect(self.progress_dialog.close)
        self.worker.start()

    def update_attempts_display(self, path):
        """Pomocnicza funkcja do aktualizacji UI o stan licznika prób."""
        if path and path.endswith('.end'):
            attempts = self.engine.get_remaining_attempts(path)
            self.status_label.setText(f"File Encrypted. Attempts: {attempts}/3")
            if attempts <= 1:
                self.status_label.setStyleSheet("color: #ff4444; font-weight: bold;")
            else:
                self.status_label.setStyleSheet("color: white;")

    def on_operation_finished(self, success, result):
        if success:
            if len(result) == 12:
                self.current_token = result
                masked = f"{result[:2]}********{result[-2:]}"
                self.token_display.setText(f"TOKEN: {masked}")
                self.copy_btn.setEnabled(True)
                self.status_label.setText("Secured.")
                self.status_label.setStyleSheet("color: #00ff00;")
            else:
                self.status_label.setText("Unlocked.")
                self.status_label.setStyleSheet("color: white;")
                self.current_token = ""
                self.token_display.setText("TOKEN: --------")
                self.copy_btn.setEnabled(False)
        else:
            # Po błędzie sprawdzamy plik ponownie, aby odświeżyć licznik prób w UI
            QMessageBox.critical(self, "Error", f"Operation failed: {result}")
            if "Remaining attempts" in result:
                # Jeśli błąd zawiera info o próbach, UI się zaktualizuje
                self.status_label.setText(result)
                self.status_label.setStyleSheet("color: #ff4444; font-weight: bold;")
            else:
                self.status_label.setText("Error occurred.")

    def handle_lock(self, path=None):
        if not path:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Selection")
            msg_box.setText("What would you like to secure?")
            btn_file = msg_box.addButton("🔐 File", QMessageBox.ButtonRole.ActionRole)
            btn_folder = msg_box.addButton("📂 Folder", QMessageBox.ButtonRole.ActionRole)
            msg_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
            msg_box.exec()
            
            if msg_box.clickedButton() == btn_file: 
                path, _ = QFileDialog.getOpenFileName(self, "Select File")
            elif msg_box.clickedButton() == btn_folder: 
                path = QFileDialog.getExistingDirectory(self, "Select Folder")
        
        if path:
            self.start_operation_worker('lock', path)

    def handle_unlock(self, path=None):
        if not path:
            path, _ = QFileDialog.getOpenFileName(self, "Select .end File", "", "UnlockEND (*.end)")
            
        if path:
            # Odświeżamy info o próbach przed wpisaniem tokena
            self.update_attempts_display(path)
            token, ok = QInputDialog.getText(self, "Token Required", "Enter Code:", QLineEdit.EchoMode.Password)
            if ok and token:
                self.start_operation_worker('unlock', path, token)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.accept()
        else: event.ignore()

    def dropEvent(self, event):
        # Po dropie sprawdzamy licznik prób
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            self.update_attempts_display(path)
        self.drop_handler.handle_drop(event)

    def closeEvent(self, event):
        if self.tray_icon and self.tray_icon.isVisible():
            self.hide()
            event.ignore()

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible(): self.hide()
            else: self.showNormal()

    def quit_application(self):
        QGuiApplication.quit()

    def copy_token_to_clipboard(self):
        if self.current_token:
            QGuiApplication.clipboard().setText(self.current_token)
            self.status_label.setText("Copied!")

    def handle_console_command(self, cmd):
        cmd_clean = cmd.lower().strip()
        if cmd_clean == "show" and self.current_token: self.logger.log(f"TOKEN: {self.current_token}")
        elif cmd_clean == "clear": self.console_widget.text_area.clear()
        elif cmd_clean == "quit": self.quit_application()

    def toggle_console(self):
        state = not self.console_widget.isVisible()
        self.console_widget.setVisible(state)
        self.resize(self.width(), 650 if state else 500)
    
    def open_file_action(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open File")
        if path:
            self.engine._open_in_system(path)

    def open_folder_action(self):
        path = QFileDialog.getExistingDirectory(self, "Open Folder")
        if path:
            self.engine._open_in_system(path)

    def show_about_dialog(self):
        QMessageBox.about(self, "About UnlockEND", 
                          "UnlockEND v1.1\n\n"
                          "Secure file and folder encryption system.\n"
                          "Optimized for CachyOS.")

    def force_key_rotation(self):
        if not self.current_token:
            QMessageBox.warning(self, "Rotation", "No active token found!")
            return
        from core.token import get_token
        self.current_token = get_token(12)
        masked = f"{self.current_token[:2]}********{self.current_token[-2:]}"
        self.token_display.setText(f"TOKEN: {masked}")
        self.logger.log("Key rotation complete.")