from client.cli import publish
from client.utils import encryption

import unittest
import tempfile
import subprocess
import json
import os
import shlex
import sys

SCRIPT = """
. {envloc}/{folder}/activate;
python ok {args}
"""

class SmokeTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.clean_env_dir = tempfile.TemporaryDirectory()
        cls.create_clean_env()

    @classmethod
    def create_clean_env(cls):
        subprocess.check_call(["virtualenv", "-q", "-p", "python", cls.clean_env_dir.name])

    def setUp(self):
        self.maxDiff = None # the errors are pretty useless if you don't do this
        self.directory = tempfile.TemporaryDirectory()
        publish.package_client(self.directory.name)

    def add_file(self, name, contents):
        with open(os.path.join(self.directory.name, name), "w") as f:
            f.write(contents)

    def make_directory(self, name):
        os.makedirs(os.path.join(self.directory.name, name))

    def run_ok(self, *args):
        command_line = SCRIPT.format(
            envloc=shlex.quote(self.clean_env_dir.name),
            folder="Scripts" if sys.platform == "win32" else "bin",
            args=" ".join(shlex.quote(arg) for arg in args),
        )
        with subprocess.Popen(
                os.getenv('SHELL', 'sh'),
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                cwd=self.directory.name, universal_newlines=True) as proc:
            stdout, stderr = proc.communicate(command_line)
        return stdout, stderr

    def add_test_ok(self):
        self.add_file("test.ok", json.dumps(
            {
                "name": "Test Assignment",
                "endpoint": "cal/cs61a/fa19/test",
                "src": [
                    "test.py"
                ],
                "tests": {
                    "tests/test.py": "ok_test"
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

    def testEncrypt(self):
        with open("demo/ok_test/config.ok") as f:
            self.add_file("test.ok", f.read())
        with open("demo/ok_test/hw1.py") as f:
            self.add_file("hw1.py", f.read())
        self.make_directory("tests")
        self.add_file("tests/__init__.py", "")
        with open("demo/ok_test/tests/q1.py") as f:
            self.add_file("tests/q1.py", f.read())
        with open("demo/ok_test/tests/q2.py") as f:
            self.add_file("tests/q2.py", f.read())

        keyfile = os.path.join(self.directory.name, "keyfile")
        _, stderr = self.run_ok("--generate-encryption-key", keyfile)
        self.assertEqual('', stderr)
        with open(keyfile) as f:
            keys = dict(json.load(f))

        self.assertEqual(set(keys), {'hw1.py', 'tests/q1.py', 'tests/q2.py'})
        _, stderr = self.run_ok('--encrypt', keyfile)
        self.assertEqual("", stderr)

        for path in "hw1.py", "tests/q1.py", "tests/q2.py":
            with open(os.path.join(self.directory.name, path)) as f:
                encryption.decrypt(f.read(), keys[path])

        _, stderr = self.run_ok('--decrypt', keys["hw1.py"], keys["tests/q1.py"])
        self.assertEqual("", stderr)

        for path in "hw1.py", "tests/q1.py":
            with open(os.path.join(self.directory.name, path)) as f:
                actual = f.read()
            with open(os.path.join("demo/ok_test", path)) as f:
                expected = f.read()

            self.assertEqual(actual, expected)

        with open(os.path.join(self.directory.name, "tests/q2.py")) as f:
            encryption.decrypt(f.read(), keys["tests/q2.py"])
