import json

from tests.end_to_end.end_to_end_test import EndToEndTest

TOO_MUCH_MEMORY_TEST = """
def f():
    '''
    >>> f()
    2
    '''
    return 0 * len(str(list(range(10 ** 7)))) + 2
"""

class SmokeTest(EndToEndTest):

    def add_test_ok(self):
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

    def testVersion(self):
        stdout, stderr = self.run_ok("--version")
        self.assertEqual(stderr, "")
        self.assertRegex(stdout, "^okpy==.*")

    def testUpdate(self):
        stdout, stderr = self.run_ok("--update")
        self.assertEqual(stderr, "")
        self.assertRegex(stdout, "Current version: v[0-9.]+\nOK is up to date")

    def testRunNoArgument(self):
        self.add_test_ok()
        stdout, stderr = self.run_ok("--local")
        self.assertEqual(stderr, "")
        self.assertRegex(stdout, "0 test cases passed! No cases failed")

    def testRunTooMuchMemory(self):
        self.add_test_ok()
        self.add_file("test.py", TOO_MUCH_MEMORY_TEST)
        stdout, stderr = self.run_ok("--local", "-q", "f", "--max-memory", "100")
        self.assertEqual(stderr, "")
        self.assertRegex(stdout, "MemoryError")
        self.assertRegex(stdout, "0 test cases passed before encountering first failed test case")
        stdout, stderr = self.run_ok("--local", "-q", "f", "--max-memory", "1000")
        self.assertEqual(stderr, "")
        self.assertRegex(stdout, "1 test cases passed! No cases failed")