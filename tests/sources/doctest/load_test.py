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
        self.mockModule.__name__ = self.mockFunction.__module__ = self.VALID_MODULE
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

    def _testOnlyModuleFunctions(self, filter_fn):
        fn_names = []
        mock_fns = []
        expected = []
        for i in range(3):
            fn_name = 'f{}'.format(i)
            fn_names.append(fn_name)

            mock_fn = mock.Mock()
            mock_fn.__doc__ = """
            >>> {0} + {1}
            {2}
            """.format(i, i*2, i*3)
            mock_fns.append(mock_fn)

            if filter_fn(i):
                mock_fn.__module__ = self.VALID_MODULE
                expected.append(fn_name)
            else:
                mock_fn.__module__ = 'other'

        self.mockModule.__name__ = self.VALID_MODULE
        self.mockModule.__dir__ = lambda *args: fn_names
        for fn_name, mock_fn in zip(fn_names, mock_fns):
            setattr(self.mockModule, fn_name, mock_fn)

        result = self.call_load()

        self.assertIsInstance(result, dict)
        self.assertEqual(len(expected), len(result))
        for fn_name in expected:
            self.assertIn(fn_name, result)
            self.assertIsInstance(result[fn_name], models.Doctest)

    def testOnlyModuleFunctions_allModuleFunctions(self):
        self._testOnlyModuleFunctions(lambda i: True)

    def testOnlyModuleFunctions_someModuleFunctions(self):
        self._testOnlyModuleFunctions(lambda i: i % 2 == 0)

    def testOnlyModuleFunctions_noModuleFunctions(self):
        self._testOnlyModuleFunctions(lambda i: False)
