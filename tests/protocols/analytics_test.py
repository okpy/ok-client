from client.protocols import analytics
from os import path

import mock
import unittest

class TestAnalyticsProtocol(unittest.TestCase):
    Q1 = "Question 1"
    Q2 = "Question 2"
    Q3 = "Question 3"
    Q4 = "Question 4"
    Q5 = "Question 5"
    Q6 = "Question 6"
    EC = "Extra Credit"

    def setUp(self):
        self.cmd_args = mock.Mock()
        self.cmd_args.submit = True
        self.assignment = mock.MagicMock()
        self.proto = analytics.protocol(self.cmd_args, self.assignment)
