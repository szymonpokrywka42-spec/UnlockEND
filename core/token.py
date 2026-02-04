import secrets
import string

def get_token(length: int = 12) -> str:
    """
    Generates a cryptographically secure token using ASCII characters.
    """
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))