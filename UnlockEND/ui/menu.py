from PyQt6.QtWidgets import QMenuBar, QMenu
from PyQt6.QtGui import QAction

class AppMenu(QMenuBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        # --- Menu Plik ---
        file_menu = self.addMenu("&Plik")
        
        # Tworzymy akcje pod nazwami, których oczekuje connect_actions
        self.open_file = QAction("Otwórz plik", self)
        self.open_file.setShortcut("Ctrl+O")
        
        self.open_dir = QAction("Otwórz folder", self)
        self.open_dir.setShortcut("Ctrl+Shift+O")
        
        self.exit_app = QAction("Zakończ", self)
        self.exit_app.setShortcut("Ctrl+Q")
        
        file_menu.addAction(self.open_file)
        file_menu.addAction(self.open_dir)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_app)

        # --- Menu Szyfrowanie ---
        self.crypto_menu = self.addMenu("&Szyfrowanie")
        
        self.toggle_custom_encoding = QAction("Własne kodowanie (XOR)", self)
        self.toggle_custom_encoding.setCheckable(True)
        self.toggle_custom_encoding.setChecked(True)
        
        # Nazwa dopasowana do connect_actions
        self.rotate_key = QAction("Wymuś rotację klucza", self)
        
        self.crypto_menu.addAction(self.toggle_custom_encoding)
        self.crypto_menu.addAction(self.rotate_key)

        # --- Menu Pomoc ---
        help_menu = self.addMenu("&Pomoc")
        self.about_action = QAction("O UnlockEND", self)
        help_menu.addAction(self.about_action)

    def connect_actions(self, parent):
        """Łączy akcje z metodami w MainWindow (window.py)"""
        # Zakładka PLIK
        self.open_file.triggered.connect(parent.open_file_action)
        self.open_dir.triggered.connect(parent.open_folder_action)
        self.exit_app.triggered.connect(parent.close)

        # Zakładka SZYFROWANIE
        self.rotate_key.triggered.connect(parent.force_key_rotation)

        # Zakładka POMOC
        self.about_action.triggered.connect(parent.show_about_dialog)