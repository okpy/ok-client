from client.utils import encryption
import unittest


class EncryptionTest(unittest.TestCase):
    def assertInverses(self, data):
        key = encryption.generate_key()
        ciphertext = encryption.encrypt(data, key)
        self.assertTrue(encryption.is_encrypted(ciphertext))
        self.assertEqual(
            encryption.decrypt(ciphertext, key),
            data
        )

    def encrypt_empty_test(self):
        self.assertInverses('')

    def encrypt_non_ascii(self):
        self.assertInverses('ठीक है अजगर')

    def encryption_decryption_fuzz_test(self):
        import random
        random.seed(0)
        for _ in range(100):
            data = "".join(random.choice('a-z' + '0-9' + 'A-Z') for _ in range(random.randint(0, 10)))
            self.assertInverses(data)

    def invalid_key_test(self):
        key1 = encryption.generate_key()
        key2 = encryption.generate_key()
        data = "test data 123"
        ciphertext = encryption.encrypt(data, key1)
        self.assertTrue(encryption.is_encrypted(ciphertext))
        self.assertRaises(encryption.InvalidKeyException, lambda: encryption.decrypt(ciphertext, key2))

    def key_characters_test(self):
        for _ in range(100):
            self.assertRegex(encryption.generate_key(), "^[0-9a-z]+$")
