import os
import tarfile
import shutil
import hashlib
import traceback
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal
from core.cyph_engine import CyphEngine
from core.token import get_token

class UnlockAppEngine:
    def __init__(self, logger):
        self.logger = logger
        self.cypher = CyphEngine()
        self.logger.log("UnlockAppEngine initialized (Pure Python Mode).")

    def process_file_lock(self, filepath, progress_sig=None, status_sig=None):
        if not os.path.exists(filepath):
            return None

        is_directory = os.path.isdir(filepath)
        work_path = filepath
        
        try:
            if is_directory:
                work_path = filepath.rstrip('/') + ".tmp_tar"
                self._pack_directory(filepath, work_path, progress_sig, status_sig)
            else:
                if status_sig: status_sig.emit("Reading file...")
                if progress_sig: progress_sig.emit(20)

            if status_sig: status_sig.emit("Encrypting with AES-GCM...")
            new_token = get_token(12)
            
            with open(work_path, 'rb') as f:
                data = f.read()

            encrypted_blob = self.cypher.encrypt(data, new_token)
            if progress_sig: progress_sig.emit(70)

            with open(filepath + ".end", 'wb') as f:
                f.write(encrypted_blob)

            if status_sig: status_sig.emit("Cleaning up originals...")
            if is_directory:
                shutil.rmtree(filepath)
                if os.path.exists(work_path): os.remove(work_path)
            else:
                self._secure_delete(filepath)
            
            if progress_sig: progress_sig.emit(100)
            return new_token

        except Exception as e:
            self.logger.log(f"Lock error: {e}", level="ERROR")
            return None

    def _pack_directory(self, source, output, progress_sig, status_sig):
        with tarfile.open(output, "w") as tar:
            files = []
            for root, _, filenames in os.walk(source):
                for f in filenames:
                    files.append(os.path.join(root, f))
            
            total = len(files)
            for i, f_path in enumerate(files):
                arcname = os.path.relpath(f_path, os.path.dirname(source))
                tar.add(f_path, arcname=arcname)
                if status_sig: status_sig.emit(f"Packing: {os.path.basename(f_path)}")
                if progress_sig and total > 0:
                    progress_sig.emit(int((i / total) * 40))

    def prepare_for_edit(self, encrypted_path, token, progress_sig=None, status_sig=None):
        try:
            if status_sig: status_sig.emit("Decrypting container...")
            if progress_sig: progress_sig.emit(30)

            with open(encrypted_path, 'rb') as f:
                blob = f.read()

            decrypted_data = self.cypher.decrypt(blob, token)
            original_path = encrypted_path.replace(".end", "")
            temp_path = original_path + ".tmp_decrypted"
            
            with open(temp_path, 'wb') as f:
                f.write(decrypted_data)

            if tarfile.is_tarfile(temp_path):
                if status_sig: status_sig.emit("Restoring folder structure...")
                with tarfile.open(temp_path, "r") as tar:
                    tar.extractall(path=os.path.dirname(original_path))
                os.remove(temp_path)
            else:
                os.rename(temp_path, original_path)

            if os.path.exists(encrypted_path): os.remove(encrypted_path)
            if progress_sig: progress_sig.emit(100)
            self._open_in_system(original_path)
            return original_path
        except Exception as e:
            self.logger.log(f"Unlock error: {e}", level="ERROR")
            return None

    def _open_in_system(self, filepath):
        try:
            os.startfile(filepath) if os.name == 'nt' else subprocess.Popen(['xdg-open', filepath])
        except: pass

    def _secure_delete(self, filepath):
        if os.path.exists(filepath) and os.path.isfile(filepath):
            size = os.path.getsize(filepath)
            with open(filepath, 'wb') as f:
                c = 0
                while c < size:
                    chunk = min(4096, size - c)
                    f.write(os.urandom(chunk))
                    c += chunk
            os.remove(filepath)

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