from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA384
from Crypto.Signature import pkcs1_15


class QChatCipher:
    """
    Class that implements a simple Encryption/Decryption interface
    """
    def __init__(self, key):
        self.key = key

    def encrypt(self, plaintext):
        """
        Encrypts provided plaintext
        :param plaintext: bytes
            The data to encrypt
        :return: tuple
            Nonce, ciphertext, tag of the AES-GCM encrypted message
        """
        aes = AES.new(self.key, AES.MODE_GCM)
        nonce = aes.nonce
        ciphertext, tag = aes.encrypt_and_digest(plaintext)
        return nonce, ciphertext, tag

    def decrypt(self, message):
        """
        Decrypts the nonce, ciphertext, tag of the encrypted message
        :param message: tuple
            Nonce, ciphertext, tag
        :return: bytes
            The plaintext of the encrypted data
        """
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
        """
        Returns the public key of the signing instance
        :return: bytes
            The public key
        """
        return self.key.publickey().exportKey()

    def sign(self, data):
        """
        Signs a piece of data using the stored key
        :param data: bytes
            Data to be signed
        :return: bytes
            Signature of the data
        """
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
        """
        Verifies the signature against the provided piece of data
        :param data: bytes
            The data that was signed
        :param sig: bytes
            The signature associated with the data
        :return: bool
            Whether verification passed or not
        """
        hash_obj = SHA384.new(data)
        verifier = pkcs1_15.new(self.pubkey)
        try:
            verifier.verify(hash_obj, sig)
            return True
        except Exception:
            return False
