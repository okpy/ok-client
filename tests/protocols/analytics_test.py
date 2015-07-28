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


    def call_check_start(self, files):
        question_status = self.proto.check_start(files)

        self.assertNotEqual(question_status, {})
        return question_status

    def testCheckStart_questionStarted(self):
        files = {'test1': """
            def q1():
                # BEGIN Question 1
                return "Question 1"
                # END Question 1

            def q2():
                # BEGIN Question 2
                "*** REPLACE THIS LINE ***"
                # END Question 2

            def q3():
                # BEGIN Question 3
                return "Question 3"
                # END Question 3
            """}
        self.assertEqual({
            self.Q1: True,
            self.Q2: False,
            self.Q3: True
        }, self.call_check_start(files))

    def testCheckStart_withReplaceComment(self):
        files = {'test1': """
            def q1():
                # BEGIN Question 1
                return "Question 1"
                # END Question 1

            def q2():
                # BEGIN Question 2
                return "Question 2" # Replace this line
                # END Question 2

            def q3():
                # BEGIN Question 3
                return "Question 3"
                # END Question 3
            """}
        self.assertEqual({
            self.Q1: True,
            self.Q2: False,
            self.Q3: True
        }, self.call_check_start(files))

    def testCheckStart_missingBeginTag(self):
        files = {'test1': """
            def q1():
                # END Question 1

            def q2():
                # END Question 2

            def q3():
                # BEGIN Question 3
                "*** REPLACE THIS LINE ***"
                # END Question 3
            """}
        self.assertEqual({
            self.Q3: False
        }, self.call_check_start(files))

    def testCheckStart_missingEndTag(self):
        files = {'test1': """
            def q1():
                # BEGIN Question 1
                "*** REPLACE THIS LINE ***"
                # END Question 1

            def q2():
                # BEGIN Question 2

            def q3():
                # BEGIN Question 3
            """}
        self.assertEqual({
            self.Q1: False,
        }, self.call_check_start(files))

    def testCheckStart_missingAllTags(self):
        files = {'test1': """
            def q1():
                # BEGIN Question 1
                "*** REPLACE THIS LINE ***"
                # END Question 1

            def q2():
                return 0 # Replace this line

            def q3():
                # BEGIN Question 3
                "*** REPLACE THIS LINE ***"
                # END Question 3
            """}
        self.assertEqual({
            self.Q1: False,
            self.Q3: False
        }, self.call_check_start(files))

    def testCheckStart_multipleFilesWithIndividualQuestions(self):
        files = {'test1': """
            def q1():
                # BEGIN Question 1
                return "Question 1"
                # END Question 1

            def q2():
                # BEGIN Question 2
                "*** REPLACE THIS LINE ***"
                # END Question 2

            def q3():
                # BEGIN Question 3
                return "Question 3"
                # END Question 3
            """,
            'test2': """
            def q4():
                # BEGIN Question 4
                return "q4"
                # END Question 4

            def q5():
                # BEGIN Question 5
                "*** REPLACE THIS LINE ***"
                # END Question 5

            def q6():
                # BEGIN Question 6
                return "q6" # Replace this line
                # END Question 6
            """}

        self.assertEqual({
            self.Q1: True,
            self.Q2: False,
            self.Q3: True,
            self.Q4: True,
            self.Q5: False,
            self.Q6: False,
        }, self.call_check_start(files))


    def testCheckStart_multipleFilesWithSharedQuestions(self):
        files = {'test1': """
            def q1_1():
                # BEGIN Question 1
                return "Question 1"
                # END Question 1

            def q2_1():
                # BEGIN Question 2
                "*** REPLACE THIS LINE ***"
                # END Question 2

            def q3_1():
                # BEGIN Question 3
                return "Question 3"
                # END Question 3

            def ec_1():
                # BEGIN Extra Credit
                "*** REPLACE THIS LINE ***"
                # END Extra Credit

            """,
            'test2': """
            def q1_2():
                # BEGIN Question 1
                return "q1"
                # END Question 1

            def q2_2():
                # BEGIN Question 2
                "*** REPLACE THIS LINE ***"
                # END Question 2

            def q3_2():
                # BEGIN Question 3
                return "q6" # Replace this line
                # END Question 3

            def ec_2():
                # BEGIN Extra Credit
                return "ec"
                # END Extra Credit
            """}

        self.assertEqual({
            self.Q1: True,
            self.Q2: False,
            self.Q3: True,
            self.EC: True
        }, self.call_check_start(files))

    def testCheckStart_schemeCode(self):
        files = {'test1': """
            (define (q1)
                ; BEGIN Question 1
                'REPLACE-THIS-LINE
                ; END Question 1
            )

            (define (q2)
                ; BEGIN Question 2
                0 ; Replace this line
                ; END Question 2
            )

            (define (q3)
                ; BEGIN Question 3
                'QUESTION-3
                ; END Question 3
            )
            """}
        self.assertEqual({
            self.Q1: False,
            self.Q2: False,
            self.Q3: True
        }, self.call_check_start(files))
