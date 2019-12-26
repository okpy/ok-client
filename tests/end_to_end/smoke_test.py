from client.cli import publish
import unittest
import tempfile
import subprocess
import os
import shlex

SCRIPT = """
source {envloc}/{folder}/activate;
python ok {args} > {stdoutloc} 2> {stderrloc}
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
        self.directory = tempfile.mkdtemp()
        publish.package_client(self.directory)

    def run_ok(self, *args):
        _, out_loc = tempfile.mkstemp()
        _, err_loc = tempfile.mkstemp()
        command_line = SCRIPT.format(
            envloc=shlex.quote(self.clean_env_loc),
            folder="scripts" if os.name == "nt" else "bin",
            args=" ".join(shlex.quote(arg) for arg in args),
            stdoutloc=shlex.quote(out_loc),
            stderrloc=shlex.quote(err_loc)
        )
        subprocess.check_output(os.getenv('SHELL', 'sh'), input=command_line.encode('utf-8'), cwd=self.directory)
        with open(out_loc) as out, open(err_loc) as err:
            return out.read(), err.read()

    def testVersion(self):
        stdout, stderr = self.run_ok("--version")
        self.assertEqual(stderr, "")
        self.assertRegex(stdout, "^okpy==.*")

    def testUpdate(self):
        stdout, stderr = self.run_ok("--update")
        self.assertEqual(stderr, "")
        self.assertRegex(stdout, "Current version: v[0-9.]+\nChecking for software updates...\nOK is up to date")
