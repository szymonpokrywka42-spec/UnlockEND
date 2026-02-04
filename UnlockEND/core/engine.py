import os
import subprocess
import hashlib
import traceback
from core.cyph_engine import CyphEngine
from core.token import get_token

class UnlockAppEngine:
    def __init__(self, logger):
        """
        Inicjalizacja silnika z przekazanym obiektem ConsoleLogic.
        """
        self.logger = logger
        self.cypher = CyphEngine()
        self.logger.log("Silnik UnlockAppEngine zainicjalizowany poprawnie (Obsługa Plików/Folderów).")

    def process_file_lock(self, filepath: str) -> str:
        """
        Pełny proces blokowania. Obsługuje zarówno pojedyncze pliki, jak i całe foldery.
        """
        if not os.path.exists(filepath):
            self.logger.log(f"BŁĄD: Ścieżka {filepath} nie istnieje.", level="ERROR")
            return None

        is_directory = os.path.isdir(filepath)
        work_path = filepath
        
        try:
            self.logger.log(f"Rozpoczynam proces LOCK dla: {os.path.basename(filepath)}")
            
            # 1. Jeśli to folder, pakujemy go do tymczasowego archiwum TAR
            if is_directory:
                self.logger.log("Wykryto folder. Kompresowanie do strumienia binarnego (TAR)...")
                work_path = filepath.rstrip('/') + ".tmp_tar"
                # tar -cf <cel> -C <katalog_nadrzedny> <nazwa_folderu>
                subprocess.run(['tar', '-cf', work_path, '-C', os.path.dirname(filepath), os.path.basename(filepath)], check=True)

            # 2. Generowanie tokena
            new_token = get_token(12)
            self.logger.log(f"Wygenerowano nowy token dla {'folderu' if is_directory else 'pliku'}.")
            
            # 3. Odczyt danych (z pliku lub z tymczasowego TARa)
            with open(work_path, 'rb') as f:
                data = f.read()
            self.logger.log(f"Wczytano {len(data)} bajtów do zaszyfrowania.")

            # 4. Szyfrowanie
            self.logger.log("Uruchamiam CyphEngine (AES-GCM)...")
            encrypted_blob = self.cypher.encrypt(data, new_token)

            # 5. Zapis kontenera .end
            target_path = filepath + ".end"
            with open(target_path, 'wb') as f:
                f.write(encrypted_blob)
            self.logger.log(f"Zapisano kontener: {os.path.basename(target_path)}")

            # 6. Sprzątanie oryginałów
            if is_directory:
                self.logger.log(f"Usuwanie oryginalnego folderu: {filepath}")
                subprocess.run(['rm', '-rf', filepath], check=True)
                if os.path.exists(work_path):
                    os.remove(work_path)
            else:
                self.logger.log("Uruchamiam procedurę bezpiecznego usuwania pliku...")
                self._secure_delete(filepath)
            
            self.logger.log("Operacja LOCK zakończona sukcesem.")
            return new_token

        except Exception as e:
            self.logger.log(f"KRYTYCZNY BŁĄD PODCZAS LOCKOWANIA: {str(e)}", level="ERROR")
            self.logger.log(traceback.format_exc(), level="DEBUG")
            return None

    def prepare_for_edit(self, encrypted_path: str, token: str) -> str:
        """
        Odszyfrowuje kontener. Jeśli wykryje, że to folder (TAR), rozpakuje go.
        """
        self.logger.log(f"Rozpoczynam UNLOCK dla: {os.path.basename(encrypted_path)}")
        try:
            with open(encrypted_path, 'rb') as f:
                blob = f.read()

            # 1. Deszyfrowanie
            self.logger.log("Deszyfrowanie danych...")
            decrypted_data = self.cypher.decrypt(blob, token)
            
            # 2. Przywrócenie ścieżki (usuwamy .end)
            original_path = encrypted_path.replace(".end", "")
            
            # 3. Zapisujemy tymczasowo, żeby sprawdzić typ pliku
            with open(original_path, 'wb') as f:
                f.write(decrypted_data)

            # 4. Sprawdzamy czy to archiwum TAR (folder)
            try:
                # Sprawdzamy typ pliku poleceniem systemowym
                file_type = subprocess.check_output(['file', original_path], text=True).lower()
                
                if "tar archive" in file_type:
                    self.logger.log("Wykryto strukturę folderu. Rozpakowywanie...")
                    # Rozpakowujemy TAR w tym samym miejscu
                    subprocess.run(['tar', '-xf', original_path, '-C', os.path.dirname(original_path)], check=True)
                    os.remove(original_path) # Usuwamy tymczasowy plik TAR
                    self.logger.log("Folder przywrócony pomyślnie.")
                else:
                    self.logger.log("Przywrócono jako pojedynczy plik.")
            except Exception as tar_err:
                self.logger.log(f"Info: Standardowe przywracanie pliku ({tar_err})", level="DEBUG")

            # 5. Usuwamy kontener .end i otwieramy wynik
            os.remove(encrypted_path)
            self._open_in_system(original_path)
            
            return original_path

        except Exception as e:
            self.logger.log(f"BŁĄD PODCZAS UNLOCKOWANIA: {str(e)}", level="ERROR")
            self.logger.log(traceback.format_exc(), level="DEBUG")
            return None

    def _open_in_system(self, filepath: str):
        try:
            # Działa zarówno dla plików (edytor), jak i folderów (menedżer plików)
            subprocess.Popen(['xdg-open', filepath])
            self.logger.log(f"Otwarto {os.path.basename(filepath)} w systemie.")
        except Exception as e:
            self.logger.log(f"Błąd xdg-open: {e}", level="WARNING")

    def _secure_delete(self, filepath: str):
        """Nadpisuje plik losowymi danymi przed usunięciem."""
        if os.path.exists(filepath) and os.path.isfile(filepath):
            try:
                size = os.path.getsize(filepath)
                with open(filepath, 'wb') as f:
                    f.write(os.urandom(size))
                os.remove(filepath)
            except Exception as e:
                self.logger.log(f"Secure delete failed: {e}", level="WARNING")
                os.remove(filepath)

    def get_file_hash(self, filepath: str) -> str:
        # Metoda pomocnicza, jeśli ścieżka to folder, zwraca hash nazwy (uproszczenie)
        if os.path.isdir(filepath):
            return hashlib.sha256(filepath.encode()).hexdigest()
            
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()