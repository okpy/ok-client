from client.protocols import backup
import mock
import unittest

class TestFileContentsProtocol(unittest.TestCase):
    def setUp(self):
        self.cmd_args = mock.Mock()
        self.assignment = mock.MagicMock()
        self.files = {}

        self.proto = backup.protocol(self.cmd_args, self.assignment)
        self.proto.is_file = self.mockIsFile
        self.proto.read_file = self.mockReadFile

    def testOnStart_emptySourceList(self):
        self.assignment.src = []
        self.assertEqual({}, self.proto.on_start())

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
        self.assertEqual(self.files, self.proto.on_start())

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
        }, self.proto.on_start())

    def testOnStart_duplicateSources(self):
        self.assignment.src = [
            'file1',
            'file1',    # file1 twice
        ]
        self.files = {
            'file1': 'contents 1',
        }
        self.assertEqual(self.files, self.proto.on_start())

    def mockIsFile(self, filepath):
        return filepath in self.files

    def mockReadFile(self, filepath):
        return self.files[filepath]

