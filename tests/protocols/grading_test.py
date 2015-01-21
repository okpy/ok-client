"""Tests the UnlockProtocol."""

from client.protocols import grading
import mock
import unittest

class GradingProtocolTest(unittest.TestCase):
    def setUp(self):
        self.cmd_args = mock.Mock()
        self.assignment = mock.Mock()
        self.proto = grading.protocol(self.cmd_args, self.assignment)

    def testOnInteract(self):
        results = self.proto.on_interact()
        self.assertIsInstance(results, dict)

