from client.utils import output
import sys
import unittest

class OutputLoggerTest(unittest.TestCase):
    MESSAGE1 = 'message 1'
    MESSAGE2 = 'message 2'

    def setUp(self):
        # nosetests captures sys.stdout, but so do we
        self.stdout = sys.stdout
        sys.stdout = output._logger = output._OutputLogger(stdout=self.stdout)

    def tearDown(self):
        sys.stdout = self.stdout

    def testRegisterLog_oneLog_outputOn(self):
        output.on()
        log_id = output.new_log()

        print(self.MESSAGE1)
        print(self.MESSAGE2)

        log = output.get_log(log_id)
        output.remove_log(log_id)

        self.assertEqual([self.MESSAGE1, "\n", self.MESSAGE2, "\n"], log)

    def testRegisterLog_manyLogs_outputOn(self):
        output.on()
        log_id1 = output.new_log()
        log_id2 = output.new_log()

        print(self.MESSAGE1)

        log1 = output.get_log(log_id1)
        log2 = output.get_log(log_id2)
        output.remove_log(log_id1)

        self.assertEqual([self.MESSAGE1, "\n"], log1)
        self.assertEqual([self.MESSAGE1, "\n"], log2)

        print(self.MESSAGE2)

        log2 = output.get_log(log_id2)
        output.remove_log(log_id2)
        self.assertEqual([self.MESSAGE1, "\n"], log1)
        self.assertEqual([self.MESSAGE1, "\n", self.MESSAGE2, "\n"], log2)

    def testRegisterLog_oneLog_outputOff(self):
        output.off()
        log_id = output.new_log()

        print(self.MESSAGE1)
        print(self.MESSAGE2)

        log = output.get_log(log_id)
        output.remove_log(log_id)

        self.assertEqual([self.MESSAGE1, "\n", self.MESSAGE2, "\n"], log)

    def testRegisterLog_manyLogs_outputOff(self):
        output.off()
        log_id1 = output.new_log()
        log_id2 = output.new_log()

        print(self.MESSAGE1)

        log1 = output.get_log(log_id1)
        log2 = output.get_log(log_id2)
        output.remove_log(log_id1)

        self.assertEqual([self.MESSAGE1, "\n"], log1)
        self.assertEqual([self.MESSAGE1, "\n"], log2)

        print(self.MESSAGE2)

        log2 = output.get_log(log_id2)
        output.remove_log(log_id2)
        self.assertEqual([self.MESSAGE1, "\n"], log1)
        self.assertEqual([self.MESSAGE1, "\n", self.MESSAGE2, "\n"], log2)
