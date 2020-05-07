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

    def testDecryptWithEndpoints(self):
        self.copy_examples()

        keys = self.encrypt_all("hw1.py", "tests/q1.py", "tests/q2.py")

        self.set_decrypt_endpoint("https://google.com/404")

        stdout, stderr = self.run_ok('--decrypt')
        self.assertEqual('', stderr)
        self.assertRegex(stdout, "Could not load decryption page .*: 404.\n"
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

        stdout, stderr = self.run_ok()
        self.assertIn("Please paste the key", stdout)
        self.assertEqual("", stderr)

        self.set_decrypt_endpoint(self.get_endpoint_returning(",".join(keys.values())))

        stdout, stderr = self.run_ok()
        self.assertNotIn("Please paste the key", stdout)
        self.assertEqual("", stderr)

        for path in "hw1.py", "tests/q1.py", "tests/q2.py":
            self.assertSameAsDemo(path)
