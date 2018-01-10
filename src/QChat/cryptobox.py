from Crypto.Cipher import AES
from Crypto.PublicKey import DSA
from Crypto.Hash import SHA256


class QChatCipher:
    def __init__(self, key):
        self.key = key

    def encrypt(self, plaintext):
        aes = AES.new(self.key, AES.MODE_GCM)
        nonce = aes.nonce
        ciphertext, tag = aes.encrypt_and_digest(plaintext)
        return (nonce, ciphertext, tag)

    def decrypt(self, message):
        nonce, ciphertext, tag = message
        aes = AES.new(self.key, AES.MODE_GCM, nonce)
        plaintext = aes.decrypt(ciphertext)
        aes.verify(tag)
        return plaintext


class QChatSigner:
    def __init__(self, key=None):
        self.key = DSA.generate(2048) if not key else key

    def get_pub(self):
        return self.key.publickey().exportKey(self.key)

    def sign(self, data):
        hash_obj = SHA256.new(data)
        signature = self.key.sign(hash_obj)
        return signature


class QChatVerifier:
    def __init__(self, pubkey):
        self.pubkey = pubkey

    def verify(self, data):
        hash_obj = SHA256.new(data)
        return self.pubkey.verify(hash_obj)
