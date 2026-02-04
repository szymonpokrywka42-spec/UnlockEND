from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel, QLineEdit
from PyQt6.QtCore import Qt, pyqtSignal

class DebugConsoleWidget(QWidget):
    # Sygnał, który wyślemy, gdy użytkownik naciśnie Enter
    command_submitted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 1. Header
        self.header = QLabel(" >_ UNLOCK_END_TERMINAL (F12 to hide)")
        self.header.setStyleSheet("background: #1a1a1a; color: #00ff00; padding: 5px; font-weight: bold;")
        
        # 2. Output area
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setStyleSheet("background: #050505; color: #00ff00; border: none; font-family: monospace;")
        
        # 3. Input area (TU WPISUJESZ KOMENDY)
        self.input_line = QLineEdit()
        self.input_line.setStyleSheet("""
            background: #000; color: #fff; border-top: 1px solid #333; 
            padding: 5px; font-family: monospace;
        """)
        self.input_line.setPlaceholderText("Wpisz komendę (np. help, clear, status)...")
        self.input_line.returnPressed.connect(self._on_return)

        layout.addWidget(self.header)
        layout.addWidget(self.text_area)
        layout.addWidget(self.input_line)

    def _on_return(self):
        cmd = self.input_line.text().strip()
        if cmd:
            self.append_log(f"<b style='color: white;'># {cmd}</b>") # Echo komendy
            self.command_submitted.emit(cmd)
            self.input_line.clear()

    def append_log(self, message):
        self.text_area.append(message)
        self.text_area.verticalScrollBar().setValue(self.text_area.verticalScrollBar().maximum())