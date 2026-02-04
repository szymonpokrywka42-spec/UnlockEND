import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id

class CyphEngine:
    def __init__(self):
        # Argon2id parameters - Optimized for security/performance balance
        self.salt_size = 16
        self.nonce_size = 12
        self.iterations = 2
        self.memory_cost = 65536  # 64MB RAM usage
        self.parallelism = 1

    def _derive_key(self, token: str, salt: bytes) -> bytes:
        """Derives a 256-bit key from a token using Argon2id."""
        kdf = Argon2id(
            salt=salt,
            length=32,
            iterations=self.iterations,
            memory_cost=self.memory_cost,
            lanes=4,
        )
        return kdf.derive(token.encode())

    def _apply_layer(self, data: bytes) -> bytes:
        """Applies a custom XOR-based transformation layer."""
        encoded = bytearray(data)
        for i in range(len(encoded)):
            mask = (0xDB + i) % 256
            encoded[i] ^= mask
        return bytes(encoded)

    def _remove_layer(self, data: bytes) -> bytes:
        """Reverses the custom transformation layer."""
        decoded = bytearray(data)
        for i in range(len(decoded)):
            mask = (0xDB + i) % 256
            decoded[i] ^= mask
        return bytes(decoded)

    def encrypt(self, raw_data: bytes, token: str) -> bytes:
        """Full encryption pipeline: Transform -> Argon2id -> AES-256-GCM."""
        try:
            processed_data = self._apply_layer(raw_data)
            
            salt = os.urandom(self.salt_size)
            nonce = os.urandom(self.nonce_size)
            
            key = self._derive_key(token, salt)
            
            aesgcm = AESGCM(key)
            ciphertext = aesgcm.encrypt(nonce, processed_data, None)
            
            return salt + nonce + ciphertext
        except Exception as e:
            raise RuntimeError(f"Encryption failed: {e}")

    def decrypt(self, blob: bytes, token: str) -> bytes:
        """Full decryption pipeline: Deconstruct -> Verify -> AES-256-GCM -> Restore."""
        try:
            s, n = self.salt_size, self.nonce_size
            if len(blob) < s + n + 16:
                raise ValueError("Corrupted or malformed data container.")

            salt = blob[:s]
            nonce = blob[s:s+n]
            ciphertext = blob[s+n:]
            
            key = self._derive_key(token, salt)
            
            aesgcm = AESGCM(key)
            decrypted_data = aesgcm.decrypt(nonce, ciphertext, None)
            
            return self._remove_layer(decrypted_data)
            
        except Exception:
            # Generic error to prevent side-channel analysis
            raise ValueError("Invalid token or tampered file!")