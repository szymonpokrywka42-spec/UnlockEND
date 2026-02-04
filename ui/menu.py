from PyQt6.QtWidgets import QMenuBar, QMenu
from PyQt6.QtGui import QAction

class AppMenu(QMenuBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        # --- File Menu ---
        file_menu = self.addMenu("&File")
        
        self.open_file = QAction("Open File", self)
        self.open_file.setShortcut("Ctrl+O")
        
        self.open_dir = QAction("Open Folder", self)
        self.open_dir.setShortcut("Ctrl+Shift+O")
        
        self.exit_app = QAction("Quit", self)
        self.exit_app.setShortcut("Ctrl+Q")
        
        file_menu.addAction(self.open_file)
        file_menu.addAction(self.open_dir)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_app)

        # --- Encryption Menu ---
        self.crypto_menu = self.addMenu("&Encryption")
        
        self.toggle_custom_encoding = QAction("Custom Encoding (XOR)", self)
        self.toggle_custom_encoding.setCheckable(True)
        self.toggle_custom_encoding.setChecked(True)
        
        self.rotate_key = QAction("Force Key Rotation", self)
        
        self.crypto_menu.addAction(self.toggle_custom_encoding)
        self.crypto_menu.addAction(self.rotate_key)

        # --- Help Menu ---
        help_menu = self.addMenu("&Help")
        self.about_action = QAction("About UnlockEND", self)
        help_menu.addAction(self.about_action)

    def connect_actions(self, parent):
        """Connects menu actions to MainWindow methods."""
        # File Actions
        self.open_file.triggered.connect(parent.open_file_action)
        self.open_dir.triggered.connect(parent.open_folder_action)
        self.exit_app.triggered.connect(parent.quit_application) # Changed to our new exit logic

        # Encryption Actions
        self.rotate_key.triggered.connect(parent.force_key_rotation)

        # Help Actions
        self.about_action.triggered.connect(parent.show_about_dialog)