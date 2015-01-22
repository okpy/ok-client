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
        self.assertRaises(TypeError, self.makeDoctest, """
            >>> 4 + 5
            9
                >>> 1 + 2
                3
            """, self.FILE)
        self.assertRaises(TypeError, self.makeDoctest, """
                >>> 4 + 5
                9
            >>> 1 + 2
            3
            """, self.FILE)

    def testRun_completePass(self):
        test = self.makeDoctest("""
        >>> 2 + 3
        5
        >>> 1 + 3
        4
        """, self.FILE)
        self.assertTrue(test.run())

    def testRun_partialFail(self):
        test = self.makeDoctest("""
        >>> 2 + 3
        5
        >>> 2 + 2
        5
        """, self.FILE)
        self.assertFalse(test.run())

    def testRun_completeFail(self):
        test = self.makeDoctest("""
        >>> 1 + 3
        5
        >>> 2 + 2
        5
        """, self.FILE)
        self.assertFalse(test.run())

    def testScore_completePass(self):
        test = self.makeDoctest("""
        >>> 2 + 3
        5
        >>> 1 + 3
        4
        """, self.FILE)
        self.assertEqual(1, test.run())

    def testScore_partialFail(self):
        test = self.makeDoctest("""
        >>> 2 + 3
        5
        >>> 2 + 2
        5
        """, self.FILE)
        self.assertEqual(0, test.run())

    def testScore_completeFail(self):
        test = self.makeDoctest("""
        >>> 1 + 3
        5
        >>> 2 + 2
        5
        """, self.FILE)
        self.assertEqual(0, test.run())
