from client.api import notebook

import mock
import unittest

class NotebookTest(unittest.TestCase):
    VALID_CONFIG = """
    {
        "name": "California Water Usage",
        "endpoint": "ok/test/su16/ex",
        "src": [
            "hw1.ipynb"
        ],
        "tests": {
            "ok_tests/q*.py": "ok_test"
        },
        "protocols": [
            "file_contents",
            "grading",
            "scoring",
            "backup"
        ]
    }
    """

    def setUp(self):
        self.is_file_patcher = mock.patch('os.path.isfile')
        self.mock_is_file = self.is_file_patcher.start()
        self.mock_is_file.return_value = True

        self.import_module_patcher = mock.patch('importlib.import_module')
        self.mock_import_module = self.import_module_patcher.start()

    def tearDown(self):
        self.is_file_patcher.stop()
        self.import_module_patcher.stop()

    def testLoadNotebook(self):
        mock_open = mock.mock_open(read_data=self.VALID_CONFIG)
        with mock.patch('builtins.open', mock_open):
            with mock.patch('client.api.assignment.Assignment') as mock_assign:
                nb = notebook.Notebook('some_config.ok')
        # Verify config file was actually opened.
        mock_open.assert_called_with('some_config.ok', 'r')
        mock_open().read.assert_called_once_with()

