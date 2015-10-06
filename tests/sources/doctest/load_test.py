from client import exceptions as ex
from client.sources import doctest
from client.sources.doctest import models
import mock
import unittest

class LoadTest(unittest.TestCase):
    VALID_FILE = 'valid.py'
    INVALID_FILE = 'invalid.ext'
    FUNCTION = 'function'
    METHOD = 'cls.method'

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

        self.cls = mock.Mock()
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
        result = self.call_load()

        self.assertIsInstance(result, dict)
        self.assertEqual(1, len(result))
        self.assertIn(self.FUNCTION, result)
        self.assertIsInstance(result[self.FUNCTION], models.Doctest)

    def testSpecificMethod(self):
        self.mockFunction.__doc__ = """
        >>> 1 + 2
        3
        """
        setattr(self.cls, self.METHOD.split('.')[1], self.mockFunction)
        setattr(self.mockModule, self.METHOD.split('.')[0], self.cls)

        result = self.call_load(name=self.METHOD)

        self.assertIsInstance(result, dict)
        self.assertEqual(1, len(result))
        self.assertIn(self.METHOD, result)
        self.assertIsInstance(result[self.METHOD], models.Doctest)
