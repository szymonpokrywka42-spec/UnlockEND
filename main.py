import sys
import os
import traceback
from PyQt6.QtWidgets import QApplication

# Importy Twoich plików
try:
    from core.engine import UnlockAppEngine
    from core.console_logic import ConsoleLogic
    from ui.window import MainWindow
    print("Importy załadowane pomyślnie...")
except Exception:
    traceback.print_exc()
    sys.exit(1)

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("UnlockEND")
    
    # Żeby apka nie zniknęła od razu przy błędzie UI
    app.setQuitOnLastWindowClosed(True)

    try:
        console_logger = ConsoleLogic()
        engine = UnlockAppEngine(logger=console_logger)
        
        print("Inicjalizacja okna...")
        window = MainWindow(engine, console_logger)
        window.show()
        print("Okno powinno być widoczne.")

        sys.exit(app.exec())
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    main()