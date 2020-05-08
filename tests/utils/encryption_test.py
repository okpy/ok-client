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
            self.assertTrue(encryption.is_valid_key(encryption.generate_key()))

    def find_single_key_test(self):
        key = encryption.generate_key()
        self.assertEqual([key], encryption.get_keys(
            "some text some text some text {} some text some text some text".format(key)))
        self.assertEqual([key], encryption.get_keys(key))

        self.assertEqual([key] * 7, encryption.get_keys(key * 7))

    def find_multiple_key_test(self):
        key_a, key_b, key_c = [encryption.generate_key() for _ in range(3)]
        self.assertEqual([key_a, key_b, key_c], encryption.get_keys(
            "Key A: {}, Key B: {}, Key C: {}".format(key_a, key_b, key_c)))
        self.assertEqual([key_a, key_c, key_b, key_a], encryption.get_keys(key_a + key_c + key_b + key_a))
