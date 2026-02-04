import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QPushButton, 
                             QLabel, QFileDialog, QMessageBox, QInputDialog, 
                             QLineEdit, QSystemTrayIcon, QMenu)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QShortcut, QKeySequence, QGuiApplication, QIcon
from ui.menu import AppMenu
from ui.console import DebugConsoleWidget

class MainWindow(QMainWindow):
    def __init__(self, engine, logger):
        super().__init__()
        self.engine = engine
        self.logger = logger
        self.current_token = ""
        
        self.init_ui()
        self.init_tray()
        
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

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.showNormal()
                self.activateWindow()

    def closeEvent(self, event):
        if self.tray_icon.isVisible():
            self.hide()
            self.tray_icon.showMessage(
                "UnlockEND",
                "Application running in background.",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
            event.ignore()

    def quit_application(self):
        self.logger.log("Shutting down...")
        QGuiApplication.quit()

    def copy_token_to_clipboard(self):
        if self.current_token:
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(self.current_token)
            self.logger.log("Token copied to clipboard.")
            self.status_label.setText("Copied!")

    def handle_console_command(self, cmd):
        cmd_clean = cmd.lower().strip()
        if cmd_clean == "help":
            self.logger.log("--- TERMINAL ---")
            self.logger.log("show   - show current session token")
            self.logger.log("clear  - clear console output")
            self.logger.log("exit   - hide main window")
            self.logger.log("quit   - terminate application")
        elif cmd_clean == "show":
            if self.current_token: self.logger.log(f"CURRENT TOKEN: {self.current_token}")
            else: self.logger.log("No active token.")
        elif cmd_clean == "clear": self.console_widget.text_area.clear()
        elif cmd_clean == "exit": self.hide()
        elif cmd_clean == "quit": self.quit_application()
        else: self.logger.log(f"Unknown command: {cmd_clean}", level="WARNING")

    def toggle_console(self):
        new_state = not self.console_widget.isVisible()
        self.console_widget.setVisible(new_state)
        if new_state:
            self.setMinimumHeight(650)
            self.resize(self.width(), 650)
        else:
            self.setMinimumHeight(500)

    def show_about_dialog(self):
        self.logger.log("About dialog opened")
        QMessageBox.about(self, "About UnlockEND", 
                          "UnlockEND v1.0\n\n"
                          "Secure file and folder encryption system.\n"
                          "Press F12 to open the terminal.\n\n"
                          "Optimized for CachyOS.")

    def handle_lock(self):
        try:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Selection")
            msg_box.setText("What would you like to secure?")
            btn_file = msg_box.addButton("🔐 File", QMessageBox.ButtonRole.ActionRole)
            btn_folder = msg_box.addButton("📂 Folder", QMessageBox.ButtonRole.ActionRole)
            msg_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
            msg_box.exec()
            
            path = None
            if msg_box.clickedButton() == btn_file: 
                path, _ = QFileDialog.getOpenFileName(self, "Select File")
            elif msg_box.clickedButton() == btn_folder: 
                path = QFileDialog.getExistingDirectory(self, "Select Folder")
            else: return

            if path:
                self.status_label.setText("Encrypting...")
                new_token = self.engine.process_file_lock(path)
                if new_token:
                    self.current_token = new_token
                    masked = f"{new_token[:2]}********{new_token[-2:]}"
                    self.token_display.setText(f"TOKEN: {masked}")
                    self.copy_btn.setEnabled(True)
                    self.status_label.setText("Secured.")
        except Exception as e: 
            self.logger.log(f"UI Error: {e}", level="ERROR")

    def handle_unlock(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select .end File", "", "UnlockEND (*.end)")
        if file_path:
            token, ok = QInputDialog.getText(self, "Token Required", "Enter Code:", QLineEdit.EchoMode.Password)
            if ok and token:
                try:
                    self.status_label.setText("Decrypting...")
                    res = self.engine.prepare_for_edit(file_path, token)
                    if res:
                        self.status_label.setText("Unlocked.")
                        self.current_token = ""
                        self.token_display.setText("TOKEN: --------")
                        self.copy_btn.setEnabled(False)
                except Exception as e: 
                    self.logger.log(f"Error: {e}", level="ERROR")

    def open_file_action(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File")
        if file_path: self.engine._open_in_system(file_path)

    def open_folder_action(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Open Folder")
        if dir_path: self.engine._open_in_system(dir_path)

    def force_key_rotation(self):
        if not self.current_token:
            QMessageBox.warning(self, "Rotation", "No active token found!")
            return
        from core.token import get_token
        new_token = get_token(12)
        self.current_token = new_token
        masked = f"{new_token[:2]}********{new_token[-2:]}"
        self.token_display.setText(f"TOKEN: {masked}")
        self.logger.log("Key rotation complete.")