from client.cli import publish
import unittest
import tempfile
import subprocess
import os

SCRIPT = """
source {envloc}/bin/activate;
python ok {args} > {stdoutloc} 2> {stderrloc}
"""

class SmokeTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.clean_env_loc = tempfile.TemporaryDirectory().name
        cls.create_clean_env()

    @classmethod
    def create_clean_env(cls):
        subprocess.check_call(["virtualenv", "-q", "-p", "python", cls.clean_env_loc])

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory().name
        publish.package_client(self.directory)

    def run_ok(self, *args):
        out_loc = tempfile.NamedTemporaryFile().name
        err_loc = tempfile.NamedTemporaryFile().name
        command_line = SCRIPT.format(
            envloc=self.clean_env_loc,
            args=" ".join(args),
            stdoutloc=out_loc,
            stderrloc=err_loc,
        )
        subprocess.call(command_line, shell=True, cwd=self.directory, executable='/bin/bash')
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
