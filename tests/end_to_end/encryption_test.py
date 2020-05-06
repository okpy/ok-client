from tests.end_to_end.end_to_end_test import EndToEndTest


class EncryptionTest(EndToEndTest):
    def testEncrypt(self):
        self.copy_examples()

        keys = self.encrypt_all("hw1.py", "tests/q1.py", "tests/q2.py")

        for path in "hw1.py", "tests/q1.py", "tests/q2.py":
            self.assertEncrypted(path, keys)

        _, stderr = self.run_ok('--decrypt', keys["hw1.py"], keys[self.pi_path("tests/q1.py")])
        self.assertEqual("", stderr)

        for path in "hw1.py", self.pi_path("tests/q1.py"):
            self.assertSameAsDemo(path)

        self.assertEncrypted("tests/q2.py", keys)
