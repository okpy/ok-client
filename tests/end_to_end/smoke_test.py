from client.cli import publish
import unittest
import tempfile
import subprocess
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

    def testVersion(self):
        stdout, stderr = self.run_ok("--version")
        self.assertEqual(stderr, "")
        self.assertRegex(stdout, "^okpy==.*")

    def testUpdate(self):
        stdout, stderr = self.run_ok("--update")
        self.assertEqual(stderr, "")
        self.assertRegex(stdout, "Current version: v[0-9.]+\nChecking for software updates...\nOK is up to date")
