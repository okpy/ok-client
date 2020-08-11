import json
import unittest

from tests.end_to_end.end_to_end_test import EndToEndTest

@unittest.skip("temporarily disabled")
class SmokeTest(EndToEndTest):

    def testVersion(self):
        stdout, stderr = self.run_ok("--version")
        self.assertEqual(stderr, "")
        self.assertRegex(stdout, "^okpy==.*")

    def testUpdate(self):
        stdout, stderr = self.run_ok("--update")
        self.assertEqual(stderr, "")
        self.assertRegex(stdout, "Current version: v[0-9.]+\n(OK is up to date|Updated to version: v[0-9.]+)")

    def testRunNoArgument(self):
        self.add_file("test.ok", json.dumps(
            {
                "name": "Test Assignment",
                "endpoint": "cal/cs61a/fa19/test",
                "src": [
                    "test.py"
                ],
                "tests": {
                    "test.py": "doctest"
                },
                "default_tests": [],
                "protocols": [
                    "restore",
                    "file_contents",
                    "unlock",
                    "grading",
                    "analytics",
                    "backup"
                ]
            }
        ))
        stdout, stderr = self.run_ok("--local")
        self.assertEqual(stderr, "")
        self.assertRegex(stdout, "0 test cases passed! No cases failed")
