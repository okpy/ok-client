from client.utils import output
import sys
import unittest
import tempfile
import subprocess

class SmokeTest(unittest.TestCase):

    def testRuns(self):
        with tempfile.TemporaryDirectory() as f:
            subprocess.check_call(['ok-publish', "-d", f])
            subprocess.check_call(['python', 'ok'], cwd=f)
