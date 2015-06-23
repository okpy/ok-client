from client.protocols import analytics
from os import path

import mock
import unittest

class TestAnalyticsProtocol(unittest.TestCase):
    def setUp(self):
        self.cmd_args = mock.Mock()
        self.cmd_args.submit = True
        self.assignment = mock.MagicMock()
        self.file_dir = path.abspath(path.join(path.dirname(__file__), '..', "data"))

        self.proto = analytics.protocol(self.cmd_args, self.assignment)

    def read_file(self, file_name):
        file_path = path.join(self.file_dir, file_name)
        print(file_path)
        with open(file_path, 'r', encoding="utf-8") as lines:
            return lines.read()

    def call_check_start(self, files):
        q_status = self.proto.check_start(files)

        self.assertNotEqual(q_status, {})
        return q_status

    def testOnCheckStart_questionStarted(self):
        files = {'test1': self.read_file("questionStarted.py")}
        self.assertEqual({
            'Question 1': True,
            'Question 2': False,
            'Question 3': True
        }, self.call_check_start(files))

    def testOnCheckStart_withReplaceComment(self):
        files = {'test1': self.read_file("withReplaceComment.py")}
        self.assertEqual({
            'Question 1': True,
            'Question 2': False,
            'Question 3': True
        }, self.call_check_start(files))

    def testOnCheckStart_missingBeginTag(self):
        files = {'test1': self.read_file("missingBeginTag.py")}
        self.assertEqual({
            'Question 1': True,
            'Question 2': True,
            'Question 3': False
        }, self.call_check_start(files))

    def testOnStart_missingEndTag(self):
        files = {'test1': self.read_file("missingEndTag.py")}
        self.assertEqual({
            'Question 1': False,
            'Question 2': True,
            'Question 3': True
        }, self.call_check_start(files))
