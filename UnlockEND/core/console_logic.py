import datetime

class ConsoleLogic:
    def __init__(self):
        # Tutaj przechowujemy funkcję z UI, która będzie wyświetlać tekst
        self.ui_callback = None
        # Bufor na logi, które wpadną zanim UI się załaduje
        self.history = []

    def set_callback(self, callback):
        """Podpina funkcję wyświetlającą z widgetu UI."""
        self.ui_callback = callback
        # Jeśli mamy jakieś logi w historii, wypchnij je od razu po podpięciu
        if self.history and self.ui_callback:
            for msg in self.history:
                self.ui_callback(msg)
            self.history.clear()

    def log(self, message, level="INFO"):
        """Główna metoda logowania."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Kolorowanie/formatowanie zależnie od poziomu
        prefix = f"[{timestamp}] [{level}]"
        formatted_msg = f"{prefix} {message}"
        
        # Jeśli UI jeszcze nie jest gotowe, zapisz do historii
        if not self.ui_callback:
            self.history.append(formatted_msg)
        else:
            self.ui_callback(formatted_msg)
            
        # Zawsze drukuj w terminalu (CachyOS/Linux console) dla pewności
        print(formatted_msg)

    def log_error(self, message):
        self.log(message, level="ERROR")

    def log_warning(self, message):
        self.log(message, level="WARNING")