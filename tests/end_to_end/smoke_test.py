from client.cli import publish
import unittest
import tempfile
import subprocess
import os
import shlex

SCRIPT = """
source {envloc}/{folder}/activate;
python ok {args}
"""

class SmokeTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.clean_env_loc = tempfile.mkdtemp()
        cls.create_clean_env()

    @classmethod
    def create_clean_env(cls):
        subprocess.check_call(["virtualenv", "-q", "-p", "python", cls.clean_env_loc])

    def setUp(self):
        self.maxDiff = None # the errors are pretty useless if you don't do this
        self.directory = tempfile.mkdtemp()
        publish.package_client(self.directory)

    def run_ok(self, *args):
        command_line = SCRIPT.format(
            envloc=shlex.quote(self.clean_env_loc),
            folder="scripts" if os.name == "nt" else "bin",
            args=" ".join(shlex.quote(arg) for arg in args),
        )
        with subprocess.Popen(
                os.getenv('SHELL', 'sh'),
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                cwd=self.directory) as proc:
            stdout, stderr = proc.communicate(command_line.encode('utf-8'))
        return stdout.decode('utf-8'), stderr.decode('utf-8')

    def testVersion(self):
        stdout, stderr = self.run_ok("--version")
        self.assertEqual(stderr, "")
        self.assertRegex(stdout, "^okpy==.*")

    def testUpdate(self):
        stdout, stderr = self.run_ok("--update")
        self.assertEqual(stderr, "")
        self.assertRegex(stdout, "Current version: v[0-9.]+\nChecking for software updates...\nOK is up to date")
