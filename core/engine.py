import os
import subprocess
import hashlib
import traceback
from PyQt6.QtCore import QThread, pyqtSignal

# Importy Twoich modułów (upewnij się, że nazwy plików się zgadzają)
from core.cyph_engine import CyphEngine
from core.token import get_token

class UnlockAppEngine:
    def __init__(self, logger):
        self.logger = logger
        self.cypher = CyphEngine()
        self.logger.log("UnlockAppEngine initialized (File/Folder handler).")

    def process_file_lock(self, filepath: str) -> str:
        """Szyfruje plik lub folder (pakuje w TAR)."""
        if not os.path.exists(filepath):
            self.logger.log(f"ERROR: Path {filepath} does not exist.", level="ERROR")
            return None

        is_directory = os.path.isdir(filepath)
        work_path = filepath
        
        try:
            self.logger.log(f"Starting LOCK process for: {os.path.basename(filepath)}")
            
            # Jeśli to folder -> pakujemy do tymczasowego TAR
            if is_directory:
                self.logger.log("Directory detected. Compressing to TAR...")
                work_path = filepath.rstrip('/') + ".tmp_tar"
                subprocess.run(['tar', '-cf', work_path, '-C', os.path.dirname(filepath), os.path.basename(filepath)], check=True)

            new_token = get_token(12)
            
            with open(work_path, 'rb') as f:
                data = f.read()

            # Szyfrowanie AES-GCM
            self.logger.log("Executing CyphEngine (AES-GCM)...")
            encrypted_blob = self.cypher.encrypt(data, new_token)

            # Zapis kontenera .end
            target_path = filepath + ".end"
            with open(target_path, 'wb') as f:
                f.write(encrypted_blob)

            # Czyszczenie po szyfrowaniu
            if is_directory:
                self.logger.log(f"Removing original directory and temp TAR: {filepath}")
                subprocess.run(['rm', '-rf', filepath], check=True)
                if os.path.exists(work_path):
                    os.remove(work_path)
            else:
                self.logger.log("Running secure delete procedure...")
                self._secure_delete(filepath)
            
            self.logger.log("LOCK operation successful.")
            return new_token

        except Exception as e:
            self.logger.log(f"CRITICAL LOCK ERROR: {str(e)}", level="ERROR")
            return None

    def prepare_for_edit(self, encrypted_path: str, token: str) -> str:
        """Odszyfrowuje kontener i przywraca plik/folder."""
        self.logger.log(f"Starting UNLOCK for: {os.path.basename(encrypted_path)}")
        try:
            with open(encrypted_path, 'rb') as f:
                blob = f.read()

            decrypted_data = self.cypher.decrypt(blob, token)
            
            # Ścieżka docelowa (np. /home/nefiu/Pulpit/fwfwqe)
            original_path = encrypted_path.replace(".end", "")
            # Tymczasowa ścieżka dla archiwum, żeby nie kolidowała z folderem!
            temp_extract_path = original_path + ".tmp_decrypted"
            
            # 1. Zapisujemy dane do pliku tymczasowego
            with open(temp_extract_path, 'wb') as f:
                f.write(decrypted_data)

            # 2. Detekcja czy to TAR
            file_info = subprocess.check_output(['file', temp_extract_path], text=True).lower()
            
            if "tar" in file_info or "archive" in file_info:
                self.logger.log("TAR structure detected. Extracting...")
                # Wypakowujemy z pliku .tmp_decrypted
                subprocess.run(['tar', '-xf', temp_extract_path, '-C', os.path.dirname(original_path)], check=True)
                # 3. Usuwamy plik tymczasowy (archiwum)
                os.remove(temp_extract_path) 
                self.logger.log("Directory restored, temp archive removed.")
            else:
                # Jeśli to nie TAR, po prostu zmieniamy nazwę na właściwą
                os.rename(temp_extract_path, original_path)
                self.logger.log("Restored as a single file.")

            # 4. USUNIĘCIE kontenera .end - teraz na pewno tu dotrze
            if os.path.exists(encrypted_path):
                os.remove(encrypted_path)
                self.logger.log(f"Removed container: {os.path.basename(encrypted_path)}")
            
            self._open_in_system(original_path)
            return original_path

        except Exception as e:
            self.logger.log(f"UNLOCK ERROR: {str(e)}", level="ERROR")
            # Sprzątanie po błędzie, żeby nie zostawiać śmieci .tmp
            if 'temp_extract_path' in locals() and os.path.exists(temp_extract_path):
                if os.path.isfile(temp_extract_path): os.remove(temp_extract_path)
            return None

    def _open_in_system(self, filepath: str):
        try:
            subprocess.Popen(['xdg-open', filepath])
        except Exception as e:
            self.logger.log(f"xdg-open error: {e}", level="WARNING")

    def _secure_delete(self, filepath: str):
        """Nadpisuje plik losowymi danymi w kawałkach przed usunięciem."""
        if os.path.exists(filepath) and os.path.isfile(filepath):
            try:
                size = os.path.getsize(filepath)
                with open(filepath, 'wb') as f:
                    remaining = size
                    while remaining > 0:
                        chunk_size = min(remaining, 4096)
                        f.write(os.urandom(chunk_size))
                        remaining -= chunk_size
                os.remove(filepath)
            except Exception:
                if os.path.exists(filepath):
                    os.remove(filepath)

# --- TURBINA (WĄTEK QTHREAD) ---

class UnlockWorker(QThread):
    status_sig = pyqtSignal(str)     # Sygnał tekstowy dla UI
    finished_sig = pyqtSignal(bool, str) # Sygnał końcowy (sukces, wynik/error)

    def __init__(self, engine, mode, filepath, token=None):
        super().__init__()
        self.engine = engine
        self.mode = mode
        self.filepath = filepath
        self.token = token

    def run(self):
        try:
            if self.mode == 'lock':
                self.status_sig.emit("🛡️ Szyfrowanie w toku...")
                res = self.engine.process_file_lock(self.filepath)
                if res:
                    self.finished_sig.emit(True, res)
                else:
                    self.finished_sig.emit(False, "Błąd blokowania (szczegóły w logach).")
            
            elif self.mode == 'unlock':
                self.status_sig.emit("🔓 Odblokowywanie...")
                res = self.engine.prepare_for_edit(self.filepath, self.token)
                if res:
                    self.finished_sig.emit(True, res)
                else:
                    self.finished_sig.emit(False, "Błąd odblokowania (zły token?).")
        except Exception as e:
            self.finished_sig.emit(False, f"Wyjątek krytyczny: {str(e)}")