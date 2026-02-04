import secrets
import string

def get_token(length: int = 12) -> str:
    """
    Generuje kryptograficznie bezpieczny 12-znakowy token.
    Mieszanka: wielkie/małe litery, cyfry i znaki specjalne.
    """
    # Definiujemy pełną pulę bezpiecznych znaków ASCII
    alphabet = string.ascii_letters + string.digits + string.punctuation
    
    # Generujemy token wybierając znaki z puli
    return ''.join(secrets.choice(alphabet) for _ in range(length))