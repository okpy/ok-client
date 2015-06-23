from client.protocols import file_contents
import mock
import unittest

class TestFileContentsProtocol(unittest.TestCase):
    def setUp(self):
        self.cmd_args = mock.Mock()
        self.cmd_args.submit = True
        self.cmd_args.export = False
        self.cmd_args.restore = False
        self.assignment = mock.MagicMock()
        self.files = {}

        self.proto = file_contents.protocol(self.cmd_args, self.assignment)
        self.proto.is_file = self.mockIsFile
        self.proto.read_file = self.mockReadFile

    def callRun(self):
        messages = {}
        self.proto.run(messages)

        self.assertIn('file_contents', messages)
        return messages['file_contents']

    def testOnStart_emptySourceList(self):
        self.assignment.src = []
        self.assertEqual({
            'submit': True,
        }, self.callRun())

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
        }, self.callRun())

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
        }, self.callRun())

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
        }, self.callRun())

    def mockIsFile(self, filepath):
        return filepath in self.files

    def mockReadFile(self, filepath):
        return self.files[filepath]

