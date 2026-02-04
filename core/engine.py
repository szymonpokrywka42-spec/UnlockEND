import os
import subprocess
import hashlib
import traceback
from core.cyph_engine import CyphEngine
from core.token import get_token

class UnlockAppEngine:
    def __init__(self, logger):
        self.logger = logger
        self.cypher = CyphEngine()
        self.logger.log("UnlockAppEngine initialized (File/Folder handler).")

    def process_file_lock(self, filepath: str) -> str:
        """
        Handles the complete locking process for both files and directories.
        """
        if not os.path.exists(filepath):
            self.logger.log(f"ERROR: Path {filepath} does not exist.", level="ERROR")
            return None

        is_directory = os.path.isdir(filepath)
        work_path = filepath
        
        try:
            self.logger.log(f"Starting LOCK process for: {os.path.basename(filepath)}")
            
            # Directory handling via TAR
            if is_directory:
                self.logger.log("Directory detected. Compressing to TAR...")
                work_path = filepath.rstrip('/') + ".tmp_tar"
                subprocess.run(['tar', '-cf', work_path, '-C', os.path.dirname(filepath), os.path.basename(filepath)], check=True)

            new_token = get_token(12)
            
            with open(work_path, 'rb') as f:
                data = f.read()
            self.logger.log(f"Loaded {len(data)} bytes for encryption.")

            # AES-GCM Encryption
            self.logger.log("Executing CyphEngine (AES-GCM)...")
            encrypted_blob = self.cypher.encrypt(data, new_token)

            # Container creation
            target_path = filepath + ".end"
            with open(target_path, 'wb') as f:
                f.write(encrypted_blob)
            self.logger.log(f"Container saved: {os.path.basename(target_path)}")

            # Cleanup
            if is_directory:
                self.logger.log(f"Removing original directory: {filepath}")
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
            self.logger.log(traceback.format_exc(), level="DEBUG")
            return None

    def prepare_for_edit(self, encrypted_path: str, token: str) -> str:
        """
        Decrypts the container and restores the file or directory.
        """
        self.logger.log(f"Starting UNLOCK for: {os.path.basename(encrypted_path)}")
        try:
            with open(encrypted_path, 'rb') as f:
                blob = f.read()

            self.logger.log("Decrypting data payload...")
            decrypted_data = self.cypher.decrypt(blob, token)
            
            original_path = encrypted_path.replace(".end", "")
            
            with open(original_path, 'wb') as f:
                f.write(decrypted_data)

            # Detect if it's a TAR archive (restored directory)
            try:
                file_type = subprocess.check_output(['file', original_path], text=True).lower()
                
                if "tar archive" in file_type:
                    self.logger.log("TAR structure detected. Extracting...")
                    subprocess.run(['tar', '-xf', original_path, '-C', os.path.dirname(original_path)], check=True)
                    os.remove(original_path) 
                    self.logger.log("Directory restored successfully.")
                else:
                    self.logger.log("Restored as a single file.")
            except Exception as tar_err:
                self.logger.log(f"Restoration info: {tar_err}", level="DEBUG")

            os.remove(encrypted_path)
            self._open_in_system(original_path)
            
            return original_path

        except Exception as e:
            self.logger.log(f"UNLOCK ERROR: {str(e)}", level="ERROR")
            self.logger.log(traceback.format_exc(), level="DEBUG")
            return None

    def _open_in_system(self, filepath: str):
        try:
            subprocess.Popen(['xdg-open', filepath])
            self.logger.log(f"Opened {os.path.basename(filepath)} via system default.")
        except Exception as e:
            self.logger.log(f"xdg-open error: {e}", level="WARNING")

    def _secure_delete(self, filepath: str):
        """Overwrites file with random bytes before deletion."""
        if os.path.exists(filepath) and os.path.isfile(filepath):
            try:
                size = os.path.getsize(filepath)
                with open(filepath, 'wb') as f:
                    f.write(os.urandom(size))
                os.remove(filepath)
            except Exception:
                os.remove(filepath)

    def get_file_hash(self, filepath: str) -> str:
        if os.path.isdir(filepath):
            return hashlib.sha256(filepath.encode()).hexdigest()
            
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()