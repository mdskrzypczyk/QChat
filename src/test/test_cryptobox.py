from QChat.cryptobox import QChatCipher, QChatSigner, QChatVerifier


class TestCryptoBox:
    @classmethod
    def setup_class(cls):
        cls.key = b"YELLOW SUBMARINE"
        cls.test_message = b"Secret Message"

    def test_cipher(self):
        cipher = QChatCipher(self.key)
        nonce, ciphertext, tag = cipher.encrypt(self.test_message)
        assert nonce != self.test_message
        assert ciphertext != self.test_message
        assert tag != self.test_message

        plaintext = cipher.decrypt((nonce, ciphertext, tag))
        assert plaintext == self.test_message

    def test_signer_and_verifier(self):
        signer = QChatSigner()
        pub = signer.get_pub()
        verifier = QChatVerifier(pub)

        test_data = b"Test data"
        sig = signer.sign(test_data)
        assert verifier.verify(test_data, sig)
