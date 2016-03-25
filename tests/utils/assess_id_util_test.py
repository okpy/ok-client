from client.utils import assess_id_util
from client.sources.common import models
import mock
import unittest
class GuidanceProtocolTest(unittest.TestCase):

    FIRST_TEST = '>>> foo\n'
    FIRST_ANS = ">>> foo\n"
    SECOND_TEST = 'cal/cs61a/fa15/lab01\nVeritasiness\n\n>>> True and 13\n72c74b6c7ed80d51f9fa7defbf7ed121\n# locked\n'
    SECOND_ANS = '>>> True and 13\nLOCKED_ANSWER\n'
    THIRD_TEST = 'cal/cs61a/fa15/lab01\nVeritasiness\n\n>>> True and 13\n13\n>>> False or 0\nb0754f6baafe74512d1be0bd5c8098ed\n# locked\n>>> not 10\n5dfeeb9ca37d955606d40c6553cd4956\n# locked\n>>> not None\n5154670fa295caf18cafa4245c1358a9\n# locked\n'
    THIRD_ANS = '>>> True and 13\n13\n>>> False or 0\nLOCKED_ANSWER\n>>> not 10\nLOCKED_ANSWER\n>>> not None\nLOCKED_ANSWER\n'
    FOURTH_TEST = 'cal/cs61a/fa15/lab09\nWhat would Scheme print?\n\nscm> (+ 3 5)\n8\nscm> (- 10 4)\n6\nscm> (* 7 6)\n42\nscm> (/ 28 2)\n14\nscm> (+ 1 2 3 4)\n10\nscm> (/ 8 2 2)\n2\nscm> (quotient 29 5)\n5\nscm> (remainder 29 5)\neb5438773fa3774b23f3a524c49c4eb1\n# locked\n'
    FOURTH_ANS = 'scm> (+ 3 5)\n8\nscm> (- 10 4)\n6\nscm> (* 7 6)\n42\nscm> (/ 28 2)\n14\nscm> (+ 1 2 3 4)\n10\nscm> (/ 8 2 2)\n2\nscm> (quotient 29 5)\n5\nscm> (remainder 29 5)\nLOCKED_ANSWER\n'
    FIFTH_TEST = 'cal/cs61a/fa15/lab09\nWhat would Scheme print?\n\nscm> (+ 3 5) ; comment\n8\n'
    FIFTH_ANS = 'scm> (+ 3 5)\n8\n'
    SIXTH_TEST = 'cal/cs61a/fa15/lab09\nWhat would Scheme print?\n\nscm> (and #t #t)\nTrue\n'
    SIXTH_ANS = 'scm> (and #t #t)\nTrue\n'

    ALL_TEST = [FIRST_TEST,SECOND_TEST,THIRD_TEST,FOURTH_TEST,FIFTH_TEST,SIXTH_TEST]
    ALL_ANS = [FIRST_ANS,SECOND_ANS,THIRD_ANS,FOURTH_ANS,FIFTH_ANS,SIXTH_ANS]


    def testAllInputs(self):
        for test in range(0,len(self.ALL_TEST)):
            print(test)
            canon_test = assess_id_util.canonicalize(self.ALL_TEST[test])
            self.assertEqual(self.ALL_ANS[test],canon_test)
