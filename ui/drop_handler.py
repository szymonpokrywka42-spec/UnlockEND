import os

class DropHandler:
    def __init__(self, window):
        self.window = window

    def handle_drop(self, event):
        if not event.mimeData().hasUrls():
            event.ignore()
            return

        urls = event.mimeData().urls()
        path = urls[0].toLocalFile()
        
        if os.path.exists(path):
            self.window.logger.log(f"Dropped: {os.path.basename(path)}")
            self.window.status_label.setText(f"Selected: {os.path.basename(path)}")
            self.window.pending_path = path
            
            if path.endswith(".end"):
                self.window.handle_unlock(path)
            else:
                self.window.handle_lock(path)
                
            event.accept()