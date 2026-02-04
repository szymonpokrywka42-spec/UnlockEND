import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id

class CyphEngine:
    def __init__(self):
        # Parametry Argon2id - wysoki koszt RAM chroni przed brute-force na GPU
        self.salt_size = 16
        self.nonce_size = 12
        self.iterations = 2
        self.memory_cost = 65536  # 64MB RAM
        self.parallelism = 1

    def _derive_key(self, token: str, salt: bytes) -> bytes:
        """Wyprowadza klucz 256-bitowy z 12-znakowego tokena."""
        kdf = Argon2id(
            salt=salt,
            length=32,
            iterations=self.iterations,
            memory_cost=self.memory_cost,
            lanes=4,
        )
        return kdf.derive(token.encode())

    def custom_obfuscation(self, data: bytes) -> bytes:

        encoded = bytearray(data)
        for i in range(len(encoded)):
            # Przykład: XOR z maską 0xDB + (pozycja bajtu modulo 255)
            # To sprawia, że każda pozycja w pliku ma inny 'klucz' pomocniczy.
            mask = (0xDB + i) % 256
            encoded[i] ^= mask
        
        return bytes(encoded)

    def custom_deobfuscation(self, data: bytes) -> bytes:

        decoded = bytearray(data)
        for i in range(len(decoded)):
            # W przypadku XOR operacja odwrócenia jest identyczna, 
            # ale musimy zachować tę samą maskę dla tej samej pozycji 'i'.
            mask = (0xDB + i) % 256
            decoded[i] ^= mask
            
        return bytes(decoded)

    def encrypt(self, raw_data: bytes, token: str) -> bytes:
        """Pełny proces: Custom Cyph -> Argon2id -> AES-256-GCM."""
        try:
            # 1. Warstwa autorska
            processed_data = self.custom_obfuscation(raw_data)
            
            # 2. Przygotowanie soli i nonce
            salt = os.urandom(self.salt_size)
            nonce = os.urandom(self.nonce_size)
            
            # 3. Generowanie klucza z tokena
            key = self._derive_key(token, salt)
            
            # 4. Szyfrowanie AES-GCM (zapewnia poufność i integralność)
            aesgcm = AESGCM(key)
            ciphertext = aesgcm.encrypt(nonce, processed_data, None)
            
            # Zwracamy paczkę gotową do zapisu w pliku .end
            return salt + nonce + ciphertext
        except Exception as e:
            raise RuntimeError(f"Błąd podczas szyfrowania: {e}")

    def decrypt(self, blob: bytes, token: str) -> bytes:
        """Pełny proces: Podział danych -> AES-256-GCM -> Custom De-Cyph."""
        try:
            # 1. Dekonstrukcja bloba
            s, n = self.salt_size, self.nonce_size
            if len(blob) < s + n + 16: # 16 to min. rozmiar tagu GCM
                raise ValueError("Plik jest uszkodzony lub zbyt krótki.")

            salt = blob[:s]
            nonce = blob[s:s+n]
            ciphertext = blob[s+n:]
            
            # 2. Odtworzenie klucza
            key = self._derive_key(token, salt)
            
            # 3. Deszyfrowanie i weryfikacja integralności
            aesgcm = AESGCM(key)
            decrypted_data = aesgcm.decrypt(nonce, ciphertext, None)
            
            # 4. Powrót z warstwy autorskiej do oryginału
            return self.custom_deobfuscation(decrypted_data)
            
        except Exception:
            # Zwracamy ogólny błąd, aby nie ułatwiać ataków typu side-channel
            raise ValueError("Niepoprawny token lub zmodyfikowany plik!")