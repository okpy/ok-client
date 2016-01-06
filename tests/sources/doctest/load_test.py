from client import exceptions as ex
from client.sources import doctest
from client.sources.doctest import models
import mock
import unittest

import os.path

class LoadTest(unittest.TestCase):
    VALID_FILE = 'valid.py'
    VALID_MODULE = os.path.splitext(VALID_FILE)[0]
    INVALID_FILE = 'invalid.ext'
    FUNCTION = 'function'

    def setUp(self):
        self.patcherIsFile = mock.patch('os.path.isfile')
        self.addCleanup(self.patcherIsFile.stop)
        self.mockIsFile = self.patcherIsFile.start()
        self.mockIsFile.return_value = True

        self.patcherLoadModule = mock.patch('client.sources.common.importing.load_module')
        self.addCleanup(self.patcherLoadModule.stop)
        self.mockLoadModule = self.patcherLoadModule.start()
        self.mockModule = mock.MagicMock()
        self.mockLoadModule.return_value = self.mockModule

        self.mockFunction = mock.Mock()

        self.assign = mock.Mock()

    def call_load(self, file=VALID_FILE, name=''):
        return doctest.load(file, name, self.assign)

    def testFileDoesNotExist(self):
        self.mockIsFile.return_value = False
        self.assertRaises(ex.LoadingException, self.call_load)

    def testInvalidFileType(self):
        self.assertRaises(ex.LoadingException, self.call_load,
                          file=self.INVALID_FILE)

    def testImportError(self):
        self.mockLoadModule.side_effect = Exception
        self.assertRaises(ex.LoadingException, self.call_load)

    def testNoFunctions(self):
        self.mockModule.__dir__ = lambda *args: []
        result = self.call_load()
        self.assertEqual({}, result)

    def testSpecificFunction(self):
        setattr(self.mockModule, self.FUNCTION, self.mockFunction)
        self.mockFunction.__doc__ = """
        >>> 1 + 2
        3
        """
        result = self.call_load(name=self.FUNCTION)

        self.assertIsInstance(result, dict)
        self.assertEqual(1, len(result))
        self.assertIn(self.FUNCTION, result)
        self.assertIsInstance(result[self.FUNCTION], models.Doctest)

    def testSpecificFunction_noDoctest(self):
        setattr(self.mockModule, self.FUNCTION, self.mockFunction)
        self.mockFunction.__doc__ = None
        result = self.call_load(name=self.FUNCTION)

        self.assertIsInstance(result, dict)
        self.assertEqual(1, len(result))
        self.assertIn(self.FUNCTION, result)
        self.assertIsInstance(result[self.FUNCTION], models.Doctest)

    def testAllFunctions(self):
        self.mockModule.__dir__ = lambda *args: [self.FUNCTION]
        setattr(self.mockModule, self.FUNCTION, self.mockFunction)
        self.mockFunction.__doc__ = """
        >>> 1 + 2
        3
        """
        self.mockModule.__name__ = self.mockFunction.__module__ = self.VALID_MODULE
        result = self.call_load()

        self.assertIsInstance(result, dict)
        self.assertEqual(1, len(result))
        self.assertIn(self.FUNCTION, result)
        self.assertIsInstance(result[self.FUNCTION], models.Doctest)
