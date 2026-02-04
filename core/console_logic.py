import datetime

class ConsoleLogic:
    def __init__(self):
        self.ui_callback = None
        self.history = []

    def set_callback(self, callback):
        """Connects the UI display function to the logic engine."""
        self.ui_callback = callback
        if self.history and self.ui_callback:
            for msg in self.history:
                self.ui_callback(msg)
            self.history.clear()

    def log(self, message, level="INFO"):
        """Main logging method. Formats and dispatches messages to UI or buffer."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] [{level}] {message}"
        
        if not self.ui_callback:
            self.history.append(formatted_msg)
        else:
            self.ui_callback(formatted_msg)
            
        # Always output to system terminal for debugging
        print(formatted_msg)

    def log_error(self, message):
        self.log(message, level="ERROR")

    def log_warning(self, message):
        self.log(message, level="WARNING")