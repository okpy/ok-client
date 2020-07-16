import json
import tempfile

from tests.end_to_end.end_to_end_test import EndToEndTest


class EncryptionTest(EndToEndTest):
    def testEncrypt(self):
        self.copy_examples()
        stdout, stderr = self.run_ok("-q", "q1")
        self.assertOnlyInvalidGrant(stderr)
        # mess up the shelve
        self.add_file(".ok_storage.dir", "\0")
        self.add_file(".ok_storage.bak", "\0")
        self.add_file(".ok_storage.dat", "\0")
        stdout, stderr = self.run_ok("-q", "q1")
        self.assertOnlyInvalidGrant(stderr)
