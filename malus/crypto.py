from cryptography.fernet import Fernet


class Crypto:
    def __init__(self, key):
        self._fernet = Fernet(key)

    def encrypt(self, text: any) -> str:
        return self._fernet.encrypt(str(text).encode("ASCII")).decode("ASCII")

    def decrypt(self, text: str) -> str:
        return self._fernet.decrypt(text.encode("ASCII")).decode("ASCII")
