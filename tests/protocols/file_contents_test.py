from client.protocols import file_contents
import mock
import unittest

# TODO(albert): change this to BackupProtocol once server is ready for the
# change.
class TestFileContentsProtocol(unittest.TestCase):
    def setUp(self):
        self.cmd_args = mock.Mock()
        self.cmd_args.submit = True
        self.assignment = mock.MagicMock()
        self.files = {}

        self.proto = file_contents.protocol(self.cmd_args, self.assignment)
        self.proto.is_file = self.mockIsFile
        self.proto.read_file = self.mockReadFile

    def testOnStart_emptySourceList(self):
        self.assignment.src = []
        self.assertEqual({
            'submit': True,
        }, self.proto.on_start())

    def testOnStart_validSources(self):
        self.assignment.src = [
            'file1',
            'file2',
        ]
        self.files = {
            'file1': 'contents 1',
            'file2': """
            contents
            2
            """,
        }
        self.assertEqual({
            'file1': 'contents 1',
            'file2': """
            contents
            2
            """,
            'submit': True,
        }, self.proto.on_start())

    def testOnStart_sourceInvalidFile(self):
        self.assignment.src = [
            'file1',
            'file2',
        ]
        self.files = {
            'file1': 'contents 1',
            # file2 does not exist
        }
        self.assertEqual({
            'file1': 'contents 1',
            'file2': '',
            'submit': True,
        }, self.proto.on_start())

    def testOnStart_duplicateSources(self):
        self.assignment.src = [
            'file1',
            'file1',    # file1 twice
        ]
        self.files = {
            'file1': 'contents 1',
        }
        self.assertEqual({
            'file1': 'contents 1',
            'submit': True,
        }, self.proto.on_start())

    def mockIsFile(self, filepath):
        return filepath in self.files

    def mockReadFile(self, filepath):
        return self.files[filepath]

