from Crypto.Cipher import AES
from Crypto.PublicKey import DSA
from Crypto.Hash import SHA256
from Crypto.Signature import DSS


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
        return self.key.publickey().exportKey()

    def sign(self, data):
        hash_obj = SHA256.new(data)
        signer = DSS.new(self.key, 'fips-186-3')
        signature = signer.sign(hash_obj)
        return signature


class QChatVerifier:
    def __init__(self, pubkey):
        self.pubkey = DSA.import_key(pubkey)

    def verify(self, data, sig):
        hash_obj = SHA256.new(data)
        verifier = DSS.new(self.pubkey, 'fips-186-3')
        try:
            verifier.verify(hash_obj, sig)
            return True
        except:
            return False
