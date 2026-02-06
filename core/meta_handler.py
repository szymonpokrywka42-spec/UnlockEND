import struct
import uuid
import hashlib

class MetaHandler:
    def __init__(self):
        # Format: Magic(4b) + Version(2b) + UUID(36b) + Hash(64b) + Attempts(1b) = 107 bajtów
        self.magic = b"UEND"
        self.version = b"12" # Podbijamy wersję
        self.header_format = "4s2s36s64sB" 
        self.meta_size = struct.calcsize(self.header_format)
        self.default_attempts = 3

    def _generate_validation(self, token: str, file_uuid: str) -> bytes:
        content = f"{token}{file_uuid}".encode()
        return hashlib.sha256(content).hexdigest().encode()

    def generate_header(self, token: str):
        """Generuje nowy nagłówek z pełną pulą 3 szans."""
        file_uuid_str = str(uuid.uuid4())
        v_hash = self._generate_validation(token, file_uuid_str)
        # Na końcu dodajemy liczbę prób: 3
        return struct.pack(self.header_format, self.magic, self.version, 
                           file_uuid_str.encode(), v_hash, self.default_attempts)

    def parse_header(self, raw_header, token_to_verify: str):
        """Sprawdza token i zarządza licznikiem prób."""
        try:
            magic, ver, f_uuid, stored_hash, attempts = struct.unpack(self.header_format, raw_header)
            
            if magic != self.magic:
                raise ValueError("To nie jest plik UnlockEND!")
            
            current_uuid = f_uuid.decode()
            expected_hash = self._generate_validation(token_to_verify, current_uuid)

            if stored_hash != expected_hash:
                new_attempts = attempts - 1
                if new_attempts <= 0:
                    return {"status": "DESTROY", "remaining": 0}
                
                # Zwracamy status błędu i nową liczbę prób do zapisania w pliku
                return {
                    "status": "WRONG_TOKEN", 
                    "remaining": new_attempts,
                    "uuid": current_uuid,
                    "raw_data": (magic, ver, f_uuid, stored_hash) # Potrzebne do nadpisania
                }

            return {
                "status": "OK",
                "version": ver.decode(),
                "uuid": current_uuid
            }
        except Exception as e:
            raise ValueError(f"Header Error: {str(e)}")

    def pack_updated_attempts(self, raw_tuple, new_attempts):
        """Pomocnicza funkcja do przygotowania danych do nadpisania licznika."""
        return struct.pack(self.header_format, *raw_tuple, new_attempts)