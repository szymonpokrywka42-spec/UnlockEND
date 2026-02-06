import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from cryptography.hazmat.backends import default_backend
from core.meta_handler import MetaHandler

class CyphEngine:
    def __init__(self):
        self.salt_size = 16
        self.nonce_size = 16 # AES block size for CTR
        self.iterations = 2
        self.memory_cost = 65536
        self.parallelism = 4
        self.meta = MetaHandler()
        self.full_header_size = 32 + self.meta.meta_size

    def _derive_key(self, token: str, salt: bytes) -> bytes:
        kdf = Argon2id(
            salt=salt,
            length=32,
            iterations=self.iterations,
            memory_cost=self.memory_cost,
            lanes=self.parallelism,
        )
        return kdf.derive(token.encode())

    def get_streaming_encryptor(self, token: str):
        salt = os.urandom(self.salt_size)
        nonce = os.urandom(self.nonce_size)
        
        meta_header = self.meta.generate_header(token) 
        
        key = self._derive_key(token, salt)
        cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
        
        combined_header = salt + nonce + meta_header
        return StreamingContext(cipher.encryptor(), combined_header)

    def get_streaming_decryptor(self, token: str, header: bytes):
        salt = header[:self.salt_size]
        nonce = header[self.salt_size:self.salt_size + self.nonce_size]
        key = self._derive_key(token, salt)
        
        cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
        return cipher.decryptor()

class StreamingContext:
    def __init__(self, engine, header):
        self.engine = engine
        self.header = header
        self.header_sent = False

    def update(self, data: bytes) -> bytes:
        # Custom XOR layer integrated into stream
        processed = bytearray(data)
        for i in range(len(processed)):
            processed[i] ^= (0xDB + i) % 256
        
        ciphertext = self.engine.update(bytes(processed))
        
        if not self.header_sent:
            self.header_sent = True
            return self.header + ciphertext
        return ciphertext

    def finalize(self) -> bytes:
        return self.engine.finalize()