import json
import tempfile

from tests.end_to_end.end_to_end_test import EndToEndTest


class EncryptionTest(EndToEndTest):
    def set_decrypt_endpoint(self, url):
        with open(self.rel_path("config.ok")) as f:
            data = json.load(f)
        location = tempfile.mktemp()
        data['decryption_keypage'] = url
        with open(self.rel_path("config.ok"), "w") as f:
            json.dump(data, f)
        return location

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

    def testDecryptMessages(self):
        self.copy_examples()
        keys = self.encrypt_all("hw1.py", "tests/q1.py", "tests/q2.py")

        key1, key2, key3 = keys["hw1.py"], keys[self.pi_path("tests/q1.py")], keys[self.pi_path("tests/q2.py")]
        stdout, stderr = self.run_ok('--decrypt', key1, key2)
        self.assertEqual("", stderr)
        self.assertRegex(stdout, r"decrypted hw1.py with {}".format(key1))
        self.assertRegex(stdout, r"decrypted tests[/\\]q1.py with {}".format(key2))

        self.assertRegex(stdout,
                         r"Unable to decrypt some files with the keys ({a}, {b}|{b}, {a})".format(a=key1, b=key2))
        self.assertRegex(stdout, r"Non-decrypted files: tests[/\\]q2\.py")

        stdout, stderr = self.run_ok('--decrypt', *keys.values())
        self.assertRegex(stdout, r"decrypted tests[/\\]q2.py with {}".format(key3))
        self.assertEqual("", stderr)

        stdout, stderr = self.run_ok('--decrypt', *keys.values())
        self.assertEqual("", stderr)
        self.assertIn("All files are already decrypted", stdout)

        stdout, stderr = self.run_ok('--decrypt')
        self.assertEqual("", stderr)
        self.assertIn("All files are already decrypted", stdout)

    def testDecryptWithEndpoints(self):
        self.copy_examples()

        keys = self.encrypt_all("hw1.py", "tests/q1.py", "tests/q2.py")

        self.set_decrypt_endpoint("https://google.com/404")

        stdout, stderr = self.run_ok('--decrypt')
        self.assertEqual('', stderr)
        self.assertRegex(stdout, "Could not load decryption page .*: 404 Client Error: Not Found for url: .*.\n"
                                 r"You can pass in a key directly by running python3 ok --decrypt \[KEY\]")

        for path in "hw1.py", "tests/q1.py", "tests/q2.py":
            self.assertEncrypted(path, keys)

        self.set_decrypt_endpoint(self.get_endpoint_returning(",".join(keys.values())))

        stdout, stderr = self.run_ok('--decrypt')
        self.assertEqual("", stderr)

        for path in "hw1.py", "tests/q1.py", "tests/q2.py":
            self.assertSameAsDemo(path)

    def testAutoDecrypt(self):
        self.copy_examples()

        keys = self.encrypt_all("hw1.py", "tests/q1.py", "tests/q2.py")

        self.set_decrypt_endpoint("https://google.com/404")

        stdout, stderr = self.run_ok('--no-browser')
        self.assertIn("Please paste the key", stdout)
        self.assertOnlyInvalidGrant(stderr)

        self.set_decrypt_endpoint(self.get_endpoint_returning(",".join(keys.values())))

        stdout, stderr = self.run_ok('--no-browser')
        self.assertNotIn("Please paste the key", stdout)
        self.assertOnlyInvalidGrant(stderr)

        for path in "hw1.py", "tests/q1.py", "tests/q2.py":
            self.assertSameAsDemo(path)
