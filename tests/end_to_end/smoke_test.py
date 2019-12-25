from client.cli import publish
import unittest
import tempfile
import subprocess

class SmokeTest(unittest.TestCase):

    def testRuns(self):
        with tempfile.TemporaryDirectory() as f:
            publish.package_client(f)
            subprocess.check_call(['python', 'ok', '--version'], cwd=f, stdout=None)
