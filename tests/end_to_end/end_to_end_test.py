import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
import json
from urllib.parse import urlencode

from client.cli import publish
from client.utils import encryption

SCRIPT = """
. {envloc}/{folder}/activate;
yes '' | python ok {args}
"""


@unittest.skip("temporarily disabled")
class EndToEndTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.clean_env_dir = tempfile.TemporaryDirectory()
        cls.create_clean_env()

    @classmethod
    def create_clean_env(cls):
        subprocess.check_call(["virtualenv", "-q", "-p", "python", cls.clean_env_dir.name])

    def setUp(self):
        self.maxDiff = None  # the errors are pretty useless if you don't do this
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
            args=" ".join(shlex.quote(str(arg)) for arg in args),
        )
        with subprocess.Popen(
                os.getenv('SHELL', 'sh'),
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                cwd=self.directory.name, universal_newlines=True) as proc:
            stdout, stderr = proc.communicate(command_line)
        return stdout, stderr

    def copy_examples(self, path='demo/ok_test'):
        for file in os.listdir(path):
            src = os.path.join(path, file)
            dst = os.path.join(self.directory.name, file)
            if os.path.isfile(src):
                shutil.copy(src, dst)
            else:
                shutil.copytree(src, dst)

    def rel_path(self, path):
        return os.path.join(self.directory.name, *path.split("/"))

    def pi_path(self, path):
        return os.path.join(*path.split("/"))

    def assertEncrypted(self, path, keys):
        path = self.pi_path(path)
        with open(self.rel_path(path)) as f:
            encryption.decrypt(f.read(), keys[path])

    def assertSameAsDemo(self, path):
        with open(self.rel_path(path)) as f:
            actual = f.read()
        with open(os.path.join("demo/ok_test", path)) as f:
            expected = f.read()
        self.assertEqual(actual, expected)

    def assertOnlyInvalidGrant(self, stderr):
        try:
            for line in stderr.split("\n"):
                if not line:
                    continue
                self.assertRegex(r"ERROR  \| auth.py:.* \| \{'error': 'invalid_grant'\}", line.strip())
        except:
            raise AssertionError("Stderr: {}".format(stderr))

    def encrypt_all(self, *paths, padding=None):
        keyfile = self.rel_path("keyfile")
        _, stderr = self.run_ok("--generate-encryption-key", keyfile)
        self.assertEqual('', stderr)
        with open(keyfile) as f:
            keys = dict(json.load(f))
        self.assertEqual(set(keys), {self.pi_path(path) for path in paths})
        _, stderr = self.run_ok('--encrypt', keyfile)
        self.assertEqual("", stderr)
        return keys

    @staticmethod
    def get_endpoint_returning(data):
        """
        Return a URL that when you call GET on it it returns the given data as part of the response
        """
        return "http://httpbin.org/get?{}".format(urlencode(dict(data=data)))

    def assertRegex(self, text, expected_regex, normalize_path=False, **kwargs):
        if normalize_path:
            text = text.replace("\\", "/")
        super().assertRegex(text, expected_regex, **kwargs)
