from client import exceptions as ex
from client.sources import ok_test
from client.sources.ok_test import models
import mock
import unittest

class LoadTest(unittest.TestCase):
    NAME = 'valid'
    VALID_FILE = 'test/' + NAME + '.py'
    INVALID_FILE = 'invalid.ext'

    def setUp(self):
        self.patcherIsFile = mock.patch('os.path.isfile')
        self.addCleanup(self.patcherIsFile.stop)
        self.mockIsFile = self.patcherIsFile.start()
        self.mockIsFile.return_value = True

        self.patcherLoadModule = mock.patch('client.sources.common.importing.load_module')
        self.addCleanup(self.patcherLoadModule.stop)
        self.mockLoadModule = self.patcherLoadModule.start()
        self.mockModule = self.mockLoadModule.return_value

        self.cmd_args = mock.Mock()

    def call_load(self, file=VALID_FILE):
        return ok_test.load(file, '', self.cmd_args)

    def testInvalidFileType(self):
        self.assertRaises(ex.LoadingException, self.call_load,
                          file=self.INVALID_FILE)

    def testNoSuchFile(self):
        self.mockIsFile.return_value = False
        self.assertRaises(ex.LoadingException, self.call_load)

    def testImportError(self):
        self.mockLoadModule.side_effect = Exception
        self.assertRaises(ex.LoadingException, self.call_load)

    def testSerializeError(self):
        self.mockModule.test = {'bogus': 'test'}
        self.assertRaises(ex.LoadingException, self.call_load)

    def testUsesBasenameAsName(self):
        self.mockModule.test = {
                'name': 'test',
                'points': 4.0,
                'suites': []
        }
        result = self.call_load()
        self.assertIsInstance(result, dict)
        self.assertEqual(1, len(result))
        self.assertIn(self.NAME, result)
        self.assertIsInstance(result[self.NAME], models.OkTest)

