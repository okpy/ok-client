from client.cli import publish
import unittest
import tempfile
import subprocess

class SmokeTest(unittest.TestCase):

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory().name
        publish.package_client(self.directory)

    def run_ok(self, *args):
        proc = subprocess.Popen(
            ['python', 'ok', *args],
            cwd=self.directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        return proc.stdout.read().decode("utf-8"), proc.stderr.read().decode("utf-8")

    def testVersion(self):
        stdout, stderr = self.run_ok("--version")
        self.assertRegex(stdout, "^okpy==.*")
        self.assertEqual(stderr, "")

    def testUpdate(self):
        stdout, stderr = self.run_ok("--update")
        self.assertRegex(stdout, "Current version: v[0-9.]+\nChecking for software updates...\nOK is up to date")
        self.assertEqual(stderr, "")
