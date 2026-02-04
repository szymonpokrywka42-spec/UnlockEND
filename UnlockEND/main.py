import sys
import os
from PyQt6.QtWidgets import QApplication

# Importy Twoich modułów
from core.engine import UnlockAppEngine
from core.console_logic import ConsoleLogic
from ui.window import MainWindow

def main():
    # 1. Inicjalizacja aplikacji Qt
    app = QApplication(sys.argv)
    app.setApplicationName("UnlockEND")
    
    # KLUCZOWE DLA TRAYA: 
    # Zapobiega zamknięciu aplikacji, gdy okno główne zostanie ukryte (hide).
    app.setQuitOnLastWindowClosed(False)

    # 2. Inicjalizacja LOGIKI KONSOLI (Mózg logów)
    console_logger = ConsoleLogic()

    # 3. Inicjalizacja SILNIKA (przekazujemy mu logger)
    engine = UnlockAppEngine(logger=console_logger)

    # 4. Inicjalizacja OKNA GŁÓWNEGO (przekazujemy silnik i logger)
    window = MainWindow(engine, console_logger)
    
    # Wyświetlamy okno
    window.show()

    # 5. Start pętli zdarzeń
    sys.exit(app.exec())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # W razie błędu startowego wypisujemy go w terminalu
        print(f"Krytyczny błąd podczas startu: {e}")