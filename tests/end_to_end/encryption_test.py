import json
import tempfile
import unittest

from tests.end_to_end.end_to_end_test import EndToEndTest


@unittest.skip("temporarily disabled")
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

    def testEncryptPadded(self):
        self.copy_examples()

        keyfile = self.rel_path("keyfile")
        _, stderr = self.run_ok("--generate-encryption-key", keyfile)
        self.assertEqual('', stderr)
        with open(keyfile) as f:
            keys = dict(json.load(f))

        _, stderr = self.run_ok("--encrypt", keyfile, "--encrypt-padding", 20)
        self.assertIn("Cannot pad data of length", stderr)

        _, stderr = self.run_ok("--encrypt", keyfile, "--encrypt-padding", 10 ** 4)
        self.assertEqual("", stderr)

        for path in "hw1.py", "tests/q1.py", "tests/q2.py":
            self.assertEncrypted(path, keys)

        content_lengths = []
        for path in "hw1.py", "tests/q1.py", "tests/q2.py":
            with open(self.rel_path(path)) as f:
                content_lengths.append(len(f.read()))

        self.assertEqual(1, len(set(content_lengths)))

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
        self.assertRegex(stdout, r"decrypted tests/q1.py with {}".format(key2), normalize_path=True)

        self.assertRegex(stdout, r"Unable to decrypt some files with the keys ({a}, {b}|{b}, {a})".format(a=key1, b=key2))
        self.assertRegex(stdout, r"Non-decrypted files: tests/q2\.py", normalize_path=True)

        stdout, stderr = self.run_ok('--decrypt', *keys.values())
        self.assertRegex(stdout, r"decrypted tests/q2.py with {}".format(key3), normalize_path=True)
        self.assertEqual("", stderr)

        stdout, stderr = self.run_ok('--decrypt', *keys.values())
        self.assertEqual("", stderr)
        self.assertIn("All files are decrypted", stdout)

        stdout, stderr = self.run_ok('--decrypt')
        self.assertEqual("", stderr)
        self.assertIn("All files are decrypted", stdout)

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
