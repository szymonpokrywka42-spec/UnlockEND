import os
import tarfile
import shutil
import subprocess
import struct
from PyQt6.QtCore import QThread, pyqtSignal
from core.cyph_engine import CyphEngine
from core.token import get_token

class UnlockAppEngine:
    def __init__(self, logger):
        self.logger = logger
        self.cypher = CyphEngine()
        # 256MB to złoty środek dla 1GB zużycia RAM i max prędkości SSD
        self.chunk_size = 256 * 1024 * 1024  
        self.logger.log(f"UnlockAppEngine initialized (256MB Buffer Mode).")

    def get_remaining_attempts(self, encrypted_path):
        """Szybki podgląd licznika prób bezpośrednio z nagłówka pliku .end."""
        try:
            if not os.path.exists(encrypted_path):
                return None
            
            crypto_header_size = 32
            with open(encrypted_path, 'rb') as f:
                f.seek(crypto_header_size)
                meta_raw = f.read(self.cypher.meta.meta_size)
                data = struct.unpack(self.cypher.meta.header_format, meta_raw)
                return data[-1] 
        except Exception as e:
            self.logger.log(f"Counter read error: {e}", level="ERROR")
            return 3 

    def _shred_now(self, filepath):
        """Całkowita destrukcja pliku - nadpisuje losowymi danymi przed usunięciem."""
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            with open(filepath, 'wb') as f:
                f.write(os.urandom(size))
                f.flush()
                os.fsync(f.fileno())
            os.remove(filepath)
            self.logger.log(f"FILE DESTROYED: {filepath}", level="ERROR")

    def process_file_lock(self, filepath, progress_sig=None, status_sig=None):
        is_dir = os.path.isdir(filepath)
        work_path = filepath
        if is_dir:
            if status_sig: status_sig.emit("Packing folder...")
            work_path = filepath + ".tmp_tar"
            with tarfile.open(work_path, "w") as tar:
                tar.add(filepath, arcname=os.path.basename(filepath))
        
        atomic_path = work_path + ".tmp_atomic"
        target_path = filepath + ".end"
        
        try:
            token = get_token(12)
            file_size = os.path.getsize(work_path)
            
            with open(work_path, 'rb', buffering=self.chunk_size) as f_in, \
                 open(atomic_path, 'wb', buffering=self.chunk_size) as f_out:
                encryptor = self.cypher.get_streaming_encryptor(token)
                processed = 0
                while chunk := f_in.read(self.chunk_size):
                    f_out.write(encryptor.update(chunk))
                    processed += len(chunk)
                    if progress_sig:
                        progress_sig.emit(int((processed / file_size) * 95))
                f_out.write(encryptor.finalize())
            
            if os.path.exists(target_path): os.remove(target_path)
            os.rename(atomic_path, target_path)
            
            if is_dir:
                shutil.rmtree(filepath)
                if os.path.exists(work_path): os.remove(work_path)
            else:
                os.remove(filepath)
            
            if progress_sig: progress_sig.emit(100)
            return token

        except Exception as e:
            self.logger.log(f"Lock error: {e}", level="ERROR")
            if os.path.exists(atomic_path): os.remove(atomic_path)
            if is_dir and os.path.exists(work_path): os.remove(work_path)
            return None

    def prepare_for_edit(self, encrypted_path, token, progress_sig=None, status_sig=None):
        temp_path = encrypted_path + ".tmp_dec"
        try:
            if status_sig: status_sig.emit("Checking Token Integrity...")
            crypto_header_size = 32
            full_header_size = 32 + self.cypher.meta.meta_size
            
            with open(encrypted_path, 'r+b') as f_target:
                full_header = f_target.read(full_header_size)
                if len(full_header) < full_header_size:
                    raise ValueError("File corrupted: Header too short.")

                meta_raw = full_header[crypto_header_size:]
                meta_res = self.cypher.meta.parse_header(meta_raw, token)
                
                if meta_res.get("status") == "DESTROY":
                    f_target.close()
                    self._shred_now(encrypted_path)
                    raise ValueError("PERMANENT LOSS: 3 failed attempts.")

                if meta_res.get("status") == "WRONG_TOKEN":
                    rem = meta_res["remaining"]
                    updated_meta = self.cypher.meta.pack_updated_attempts(meta_res["raw_data"], rem)
                    f_target.seek(crypto_header_size)
                    f_target.write(updated_meta)
                    f_target.flush()
                    raise ValueError(f"WRONG TOKEN! Remaining: {rem}")

                if status_sig: status_sig.emit("Token OK. Decrypting...")
                
                f_target.seek(full_header_size)
                file_size = os.path.getsize(encrypted_path) - full_header_size
                processed = 0

                with open(temp_path, 'wb', buffering=self.chunk_size) as f_out:
                    decryptor = self.cypher.get_streaming_decryptor(token, full_header[:crypto_header_size])
                    while chunk := f_target.read(self.chunk_size):
                        # 1. Deszyfrowanie AES
                        decrypted_chunk = decryptor.update(chunk)
                        
                        # 2. Przywrócenie XOR (Kluczowe dla poprawnego TAR)
                        processed_chunk = bytearray(decrypted_chunk)
                        for i in range(len(processed_chunk)):
                            processed_chunk[i] ^= (0xDB + i) % 256
                        
                        f_out.write(processed_chunk)
                        processed += len(chunk)
                        if progress_sig:
                            progress_sig.emit(int((processed / file_size) * 95))
                    f_out.write(decryptor.finalize())

            # --- ROZPAKOWYWANIE ---
            original_path = encrypted_path.replace(".end", "")
            
            # Wymuszamy sprawdzenie czy to TAR
            if tarfile.is_tarfile(temp_path):
                if status_sig: status_sig.emit("Extracting project folder...")
                extract_dir = os.path.dirname(original_path)
                with tarfile.open(temp_path, "r") as tar:
                    tar.extractall(path=extract_dir)
                os.remove(temp_path)
                final_output = original_path
            else:
                # Jeśli to był pojedynczy plik
                if os.path.exists(original_path): os.remove(original_path)
                os.rename(temp_path, original_path)
                final_output = original_path

            if os.path.exists(encrypted_path): os.remove(encrypted_path)
            if progress_sig: progress_sig.emit(100)
            self._open_in_system(final_output)
            return final_output

        except Exception as e:
            self.logger.log(f"Unlock error: {e}", level="ERROR")
            # ZOSTAWIAMY temp_path w razie błędu, żebyś mógł go ręcznie ratować
            return None
        
    def _open_in_system(self, filepath):
        try:
            if os.name == 'nt': os.startfile(filepath)
            else: subprocess.Popen(['xdg-open', filepath])
        except: pass

class UnlockWorker(QThread):
    status_sig = pyqtSignal(str)
    progress_sig = pyqtSignal(int)
    finished_sig = pyqtSignal(bool, str)

    def __init__(self, engine, mode, filepath, token=None):
        super().__init__()
        self.engine = engine
        self.mode = mode
        self.filepath = filepath
        self.token = token

    def run(self):
        try:
            if self.mode == 'lock':
                res = self.engine.process_file_lock(self.filepath, self.progress_sig, self.status_sig)
            else:
                res = self.engine.prepare_for_edit(self.filepath, self.token, self.progress_sig, self.status_sig)
            
            if res: self.finished_sig.emit(True, res)
            else: self.finished_sig.emit(False, "Operation failed.")
        except Exception as e:
            self.finished_sig.emit(False, str(e))