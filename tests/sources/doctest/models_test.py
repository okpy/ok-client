from client.sources.doctest import models
import unittest

class DoctestTest(unittest.TestCase):
    NAME = 'doctest'
    POINTS = 1
    FILE = 'operator'

    def makeDoctest(self, docstring, file, verbose=False, interactive=False):
        return models.Doctest(file, verbose, interactive, name=self.NAME,
                              points=self.POINTS, docstring=docstring)

    def testConstructor_standardDoctest(self):
        try:
            self.makeDoctest("""
            >>> 2 + 3
            5
            """, self.FILE)
        except TypeError:
            self.fail()

    def testConstructor_noDoctest(self):
        try:
            self.makeDoctest("""
            This is just a docstring
            """, self.FILE)
        except TypeError:
            self.fail()

    def testConstructor_lineBreakInDoctest(self):
        try:
            self.makeDoctest("""
            >>> 4 + 5
            9

            >>> 1 + 2
            3
            """, self.FILE)
        except TypeError:
            self.fail()

    def testConstructor_validIndentationInconsistencies(self):
        try:
            self.makeDoctest("""
                >>> 4 + 5
                9

            >>> 1 + 2
            3
            """, self.FILE)
        except TypeError:
            self.fail()

    def testConstructor_invalidIndentationInconsistencies(self):
        # TODO(albert): test not passing
        pass
        # self.assertRaises(TypeError, self.makeDoctest, """
        #     >>> 4 + 5
        #     9
        #         >>> 1 + 2
        #         3
        #     """, self.FILE)
        # self.assertRaises(TypeError, self.makeDoctest, """
        #         >>> 4 + 5
        #         9
        #     >>> 1 + 2
        #     3
        #     """, self.FILE)

    def testRun_completePass(self):
        test = self.makeDoctest("""
        >>> 2 + 3
        5
        >>> 1 + 3
        4
        """, self.FILE)
        self.assertEqual({
            'passed': 1,
            'failed': 0,
            'locked': 0,
        }, test.run())

    def testRun_partialFail(self):
        test = self.makeDoctest("""
        >>> 2 + 3
        5
        >>> 2 + 2
        5
        """, self.FILE)
        self.assertEqual({
            'passed': 0,
            'failed': 1,
            'locked': 0,
        }, test.run())

    def testRun_completeFail(self):
        test = self.makeDoctest("""
        >>> 1 + 3
        5
        >>> 2 + 2
        5
        """, self.FILE)
        self.assertEqual({
            'passed': 0,
            'failed': 1,
            'locked': 0,
        }, test.run())

    def testRun_solitaryPS1(self):
        test = self.makeDoctest("""
        >>> 1 + 2
        3
        >>>
        >>> 1
        1
        """, self.FILE)
        self.assertEqual({
            'passed': 0,
            'failed': 1,
            'locked': 0,
        }, test.run())

    def testRun_solitaryPS2(self):
        test = self.makeDoctest("""
        >>> def f():
        ...     return 4
        ...
        >>> f()
        4
        """, self.FILE)
        self.assertEqual({
            'passed': 1,
            'failed': 0,
            'locked': 0,
        }, test.run())


    def testScore_completePass(self):
        test = self.makeDoctest("""
        >>> 2 + 3
        5
        >>> 1 + 3
        4
        """, self.FILE)
        self.assertEqual(1, test.score())

    def testScore_partialFail(self):
        test = self.makeDoctest("""
        >>> 2 + 3
        5
        >>> 2 + 2
        5
        """, self.FILE)
        self.assertEqual(0, test.score())

    def testScore_completeFail(self):
        test = self.makeDoctest("""
        >>> 1 + 3
        5
        >>> 2 + 2
        5
        """, self.FILE)
        self.assertEqual(0, test.score())
