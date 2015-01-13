from client.serialize.common import serialize
import mock
import unittest

###############
# Field Tests #
###############

class MockField(serialize.Field):
    VALID_INT = 42
    INVALID_INT = 2

    def is_valid(self, value):
        return value == self.VALID_INT

    def to_json(self, value):
        value = super().to_json(value)
        return self.VALID_INT

class FieldTest(unittest.TestCase):
    def testNoArguments(self):
        field = MockField()
        self.assertEqual(field.optional, False)
        self.assertEqual(field.default, serialize.NoValue)

    def testDefaultArgument_validDefault(self):
        field = MockField(default=MockField.VALID_INT)
        self.assertEqual(field.optional, True)
        self.assertEqual(field.default, MockField.VALID_INT)

    def testDefaultArgument_invalidDefault(self):
        self.assertRaises(TypeError, MockField, default=MockField.INVALID_INT)

    def testDefaultArgument_optionalFalse(self):
        field = MockField(optional=False, default=MockField.VALID_INT)
        # Setting a default always sets optional to True
        self.assertEqual(field.optional, True)
        self.assertEqual(field.default, MockField.VALID_INT)

    def testOptional(self):
        field = MockField(optional=True)
        self.assertEqual(field.optional, True)
        self.assertEqual(field.default, serialize.NoValue)

    def testToJson_validValue(self):
        field = MockField()
        self.assertEqual(MockField.VALID_INT, field.to_json(MockField.VALID_INT))

    def testToJson_invalidValue(self):
        field = MockField()
        self.assertRaises(TypeError, field.to_json, MockField.INVALID_INT)


class ListFieldTest(unittest.TestCase):
    TEST_INT = 42

    def testConstructor_heterogeneous(self):
        field = serialize.List()
        self.assertTrue(field.is_valid([1, 'hi', 6]))

    def testConstructor_homogeneous(self):
        field = serialize.List(type=int)
        self.assertFalse(field.is_valid([1, 'hi', 6]))
        self.assertTrue(field.is_valid([1, 2, 3, 4]))

    def testConstructor_homogeneousSubclass(self):
        class IntSubclass(int):
            def __init__(self):
                pass
        field = serialize.List(type=int)
        self.assertTrue(field.is_valid([1, IntSubclass()]))

    def testConstructor_heterogeneousEmptyList(self):
        field = serialize.List()
        self.assertTrue(field.is_valid([]))

    def testConstructor_homogeneousEmptyList(self):
        field = serialize.List(type=str)
        self.assertTrue(field.is_valid([]))

    def testToJson_shallow(self):
        field = serialize.List()
        expect = [1, 'hi', True]
        self.assertEqual(expect, field.to_json(expect))

    def testToJson_recursive(self):
        field = serialize.List()
        class Recursive(object):
            def to_json(self):
                return ListFieldTest.TEST_INT
        expect = [1, self.TEST_INT, True]
        arg = [1, Recursive(), True]

        self.assertEqual(expect, field.to_json(arg))


class DictFieldTest(unittest.TestCase):
    TEST_INT = 42

    def testConstructor_heterogeneous(self):
        field = serialize.Dict()
        self.assertTrue(field.is_valid({'hi': 4, True: 'boo'}))

    def testConstructor_homogeneousKey(self):
        field = serialize.Dict(keys=int)
        self.assertFalse(field.is_valid({'hi': 4}))
        self.assertTrue(field.is_valid({4: 'hi', 2: 1}))

    def testConstructor_homogeneousValue(self):
        field = serialize.Dict(values=str)
        self.assertFalse(field.is_valid({'hi': 4, 'f': 'bye'}))
        self.assertTrue(field.is_valid({4: 'hi', 'f': 'bye'}))

    def testConstructor_homogeneousSubclass(self):
        class IntSubclass(int):
            def __init__(self):
                pass
        field = serialize.Dict(keys=int, values=int)
        self.assertTrue(field.is_valid({IntSubclass(): IntSubclass()}))

    def testConstructor_heterogeneousEmptyDict(self):
        field = serialize.Dict()
        self.assertTrue(field.is_valid({}))

    def testConstructor_homogeneousEmptyDict(self):
        field = serialize.Dict(keys=str, values=int)
        self.assertTrue(field.is_valid({}))

    def testToJson_shallow(self):
        field = serialize.Dict()
        expect = {'hi': 4, True: 3}
        self.assertEqual(expect, field.to_json(expect))

    def testToJson_recursiveKey(self):
        field = serialize.Dict()
        class Recursive(object):
            def to_json(self):
                return DictFieldTest.TEST_INT
        expect = {self.TEST_INT: 4, True: 3}
        arg = {Recursive(): 4, True: 3}

        self.assertEqual(expect, field.to_json(arg))

    def testToJson_recursiveValue(self):
        field = serialize.Dict()
        class Recursive(object):
            def to_json(self):
                return DictFieldTest.TEST_INT
        expect = {4: self.TEST_INT, True: 3}
        arg = {4: Recursive(), True: 3}

        self.assertEqual(expect, field.to_json(arg))

######################
# Serializable Tests #
######################

class MockSerializable(serialize.Serializable):
    TEST_INT = 2

    var1 = serialize.Boolean()
    var2 = serialize.Int(default=TEST_INT)
    var3 = serialize.String(optional=True)

class SerializableTest(unittest.TestCase):
    TEST_INT = 42
    TEST_BOOL = True
    TEST_STR = 'hi'

    def testConstructor_missingRequiredFields(self):
        self.assertRaises(TypeError, MockSerializable)

    def testConstructor_incorrectRequiredFields(self):
        self.assertRaises(TypeError, MockSerializable, var1=self.TEST_INT)

    def testConstructor_incorrectOptionalFields(self):
        self.assertRaises(TypeError, MockSerializable, var1=self.TEST_BOOL,
                          var2=self.TEST_BOOL)

    def testConstructor_unexpectedFields(self):
        self.assertRaises(TypeError, MockSerializable, var1=self.TEST_BOOL,
                          var2=self.TEST_INT, foo=self.TEST_INT)

    def testConstructor_validArguments(self):
        try:
            MockSerializable(var1=self.TEST_BOOL, var3=self.TEST_STR)
        except TypeError:
            self.fail("Should not have failed")

    def testSetAttr_validType(self):
        obj = MockSerializable(var1=self.TEST_BOOL, var3=self.TEST_STR)
        obj.var1 = not self.TEST_BOOL
        self.assertEqual(not self.TEST_BOOL, obj.var1)

    def testSetAttr_invalidType(self):
        obj = MockSerializable(var1=self.TEST_BOOL, var3=self.TEST_STR)
        try:
            obj.var1 = self.TEST_INT
        except TypeError:
            pass
        else:
            self.fail("Should have raised a TypeError")

    def testToJson_noOptional(self):
        obj = MockSerializable(var1=self.TEST_BOOL)
        expect = {'var1': self.TEST_BOOL, 'var2': MockSerializable.TEST_INT}
        self.assertEqual(expect, obj.to_json())

    def testToJson_withOptional(self):
        obj = MockSerializable(var1=self.TEST_BOOL, var3=self.TEST_STR)
        expect = {'var1': self.TEST_BOOL, 'var2': MockSerializable.TEST_INT,
                  'var3': self.TEST_STR}
        self.assertEqual(expect, obj.to_json())

