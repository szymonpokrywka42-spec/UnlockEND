import sys
import os
from PyQt6.QtWidgets import QApplication

from core.engine import UnlockAppEngine
from core.console_logic import ConsoleLogic
from ui.window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("UnlockEND")
    
    # Ensures the application continues running in the system tray
    app.setQuitOnLastWindowClosed(False)

    console_logger = ConsoleLogic()
    engine = UnlockAppEngine(logger=console_logger)
    
    window = MainWindow(engine, console_logger)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Critical startup error: {e}")