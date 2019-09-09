from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256, SHA384
from Crypto.Signature import DSS, pkcs1_15


class QChatCipher:
    """
    Class that implements a simple Encryption/Decryption interface
    """
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
    """
    Class that implements a simple message signing interface that can
    be retained
    """
    def __init__(self, key=None):
        self.key = RSA.generate(1024) if not key else key

    def get_pub(self):
        return self.key.publickey().exportKey()

    def sign(self, data):
        hash_obj = SHA384.new(data)
        signer = pkcs1_15.new(self.key)
        signature = signer.sign(hash_obj)
        return signature


class QChatVerifier:
    """
    Class that implements a message verification interface
    """
    def __init__(self, pubkey):
        self.pubkey = RSA.import_key(pubkey)

    def verify(self, data, sig):
        hash_obj = SHA384.new(data)
        verifier = pkcs1_15.new(self.pubkey)
        try:
            verifier.verify(hash_obj, sig)
            return True
        except:
            return False
