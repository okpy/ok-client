from client import exceptions as ex
from client.sources.common import core
import mock
import unittest

###############
# Field Tests #
###############

class MockField(core.Field):
    VALID_INT = 42
    OK_INT = 3
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
        self.assertEqual(field.default, core.NoValue)

    def testDefaultArgument_validDefault(self):
        field = MockField(default=MockField.VALID_INT)
        self.assertEqual(field.optional, True)
        self.assertEqual(field.default, MockField.VALID_INT)

    def testDefaultArgument_invalidDefault(self):
        self.assertRaises(ex.SerializeException, MockField,
                          default=MockField.INVALID_INT)

    def testDefaultArgument_optionalFalse(self):
        field = MockField(optional=False, default=MockField.VALID_INT)
        # Setting a default always sets optional to True
        self.assertEqual(field.optional, True)
        self.assertEqual(field.default, MockField.VALID_INT)

    def testOptional(self):
        field = MockField(optional=True)
        self.assertEqual(field.optional, True)
        self.assertEqual(field.default, core.NoValue)

    def testToJson_validValue(self):
        field = MockField()
        self.assertEqual(MockField.VALID_INT, field.to_json(MockField.VALID_INT))

    def testToJson_invalidValue(self):
        field = MockField()
        self.assertRaises(ex.SerializeException, field.to_json,
                          MockField.INVALID_INT)


class ListFieldTest(unittest.TestCase):
    TEST_INT = 42

    def testConstructor_heterogeneous(self):
        field = core.List()
        self.assertTrue(field.is_valid([1, 'hi', 6]))

    def testConstructor_homogeneous(self):
        field = core.List(type=int)
        self.assertFalse(field.is_valid([1, 'hi', 6]))
        self.assertTrue(field.is_valid([1, 2, 3, 4]))

    def testConstructor_homogeneousSubclass(self):
        class IntSubclass(int):
            def __init__(self):
                pass
        field = core.List(type=int)
        self.assertTrue(field.is_valid([1, IntSubclass()]))

    def testConstructor_heterogeneousEmptyList(self):
        field = core.List()
        self.assertTrue(field.is_valid([]))

    def testConstructor_homogeneousEmptyList(self):
        field = core.List(type=str)
        self.assertTrue(field.is_valid([]))

    def assertCoerce_pass(self, expect, value, **fields):
        field = core.List(**fields)
        self.assertEqual(expect, field.coerce(value))

    def assertCoerce_errors(self, value, **fields):
        field = core.List(**fields)
        self.assertRaises(ex.SerializeException, field.coerce, value)

    def testCoerce_heterogeneousList(self):
        lst = [1, 'hi', 3, True]
        self.assertCoerce_pass(lst, lst)

    def testCoerce_heterogeneousValidNonList(self):
        value = (1, 'hi', 3, True)
        expect = list(value)
        self.assertCoerce_pass(expect, value)

    def testCoerce_heterogeneousInvalidNonList(self):
        self.assertCoerce_errors(4)

    def testCoerce_homogeneousValidList(self):
        value = [1, 2, 3, 4]
        self.assertCoerce_pass(value, value, type=int)

    def testCoerce_homogeneousInvalidList(self):
        # TODO(albert): should make primitive list elements perform
        # strict coercion, to avoid unintended conversions.
        # value = [1, 2, 3, 4]
        # self.assertCoerce_errors(value, type=str)
        pass

    def testCoerce_homogeneousValidNonList(self):
        value = (1, 2, 3, 4)
        expect = list(value)
        self.assertCoerce_pass(expect, value, type=int)

    def testCoerce_homogeneousInvalidNonList_notIterable(self):
        self.assertCoerce_errors(4, type=int)

    def testCoerce_homogeneousInvalidNonList_wrongType(self):
        # TODO(albert): should make primitive list elements perform
        # strict coercion, to avoid unintended conversions.
        # value = [1, 2, 3]
        # self.assertCoerce_errors(value, type=str)
        pass

    def testToJson_shallow(self):
        field = core.List()
        expect = [1, 'hi', True]
        self.assertEqual(expect, field.to_json(expect))

    def testToJson_recursive(self):
        field = core.List()
        class Recursive(object):
            def to_json(self):
                return ListFieldTest.TEST_INT
        expect = [1, self.TEST_INT, True]
        arg = [1, Recursive(), True]

        self.assertEqual(expect, field.to_json(arg))


class DictFieldTest(unittest.TestCase):
    TEST_INT = 42

    def testConstructor_heterogeneous(self):
        field = core.Dict()
        self.assertTrue(field.is_valid({'hi': 4, True: 'boo'}))

    def testConstructor_homogeneousKey(self):
        field = core.Dict(keys=int)
        self.assertFalse(field.is_valid({'hi': 4}))
        self.assertTrue(field.is_valid({4: 'hi', 2: 1}))

    def testConstructor_homogeneousValue(self):
        field = core.Dict(values=str)
        self.assertFalse(field.is_valid({'hi': 4, 'f': 'bye'}))
        self.assertTrue(field.is_valid({4: 'hi', 'f': 'bye'}))

    def testConstructor_homogeneousSubclass(self):
        class IntSubclass(int):
            def __init__(self):
                pass
        field = core.Dict(keys=int, values=int)
        self.assertTrue(field.is_valid({IntSubclass(): IntSubclass()}))

    def testConstructor_heterogeneousEmptyDict(self):
        field = core.Dict()
        self.assertTrue(field.is_valid({}))

    def testConstructor_homogeneousEmptyDict(self):
        field = core.Dict(keys=str, values=int)
        self.assertTrue(field.is_valid({}))

    def assertCoerce_pass(self, expect, value, **fields):
        field = core.Dict(**fields)
        self.assertEqual(expect, field.coerce(value))

    def assertCoerce_errors(self, value, **fields):
        field = core.Dict(**fields)
        self.assertRaises(ex.SerializeException, field.coerce, value)

    def testCoerce_heterogeneousDict(self):
        d = {'a': 1, 2: False}
        self.assertCoerce_pass(d, d)

    def testCoerce_heterogeneousValidNonDict(self):
        value = (('a', 1), (2, False))
        expect = dict(value)
        self.assertCoerce_pass(expect, value)

    def testCoerce_heterogeneousInvalidNonDict(self):
        self.assertCoerce_errors([1, 2, 3])

    def testCoerce_homogeneousValidDict(self):
        value = {'a': 1, 'b': 2}
        self.assertCoerce_pass(value, value, keys=str, values=int)

    def testCoerce_homogeneousInvalidDict(self):
        # TODO(albert): should make primitive dict elements perform
        # strict coercion, to avoid unintended conversions.
        # value = {'a': True, 'b': False}
        # self.assertCoerce_errors(value, keys=str, values=int)
        pass

    def testCoerce_homogeneousValidNonDict(self):
        value = (('a', 1), ('b', 2))
        expect = dict(value)
        self.assertCoerce_pass(expect, value, keys=str, values=int)

    def testCoerce_homogeneousInvalidNonDict_notDictLike(self):
        self.assertCoerce_errors([1, 2, 3], keys=int)

    def testCoerce_homogeneousInvalidNonDict_wrongType(self):
        # TODO(albert): should make primitive dict elements perform
        # strict coercion, to avoid unintended conversions.
        # value = (('a', True), ('b', False))
        # self.assertCoerce_errors(value, keys=str, values=int)
        pass

    def testToJson_shallow(self):
        field = core.Dict()
        expect = {'hi': 4, True: 3}
        self.assertEqual(expect, field.to_json(expect))

    def testToJson_recursiveKey(self):
        field = core.Dict()
        class Recursive(object):
            def to_json(self):
                return DictFieldTest.TEST_INT
        expect = {self.TEST_INT: 4, True: 3}
        arg = {Recursive(): 4, True: 3}

        self.assertEqual(expect, field.to_json(arg))

    def testToJson_recursiveValue(self):
        field = core.Dict()
        class Recursive(object):
            def to_json(self):
                return DictFieldTest.TEST_INT
        expect = {4: self.TEST_INT, True: 3}
        arg = {4: Recursive(), True: 3}

        self.assertEqual(expect, field.to_json(arg))

######################
# Serializable Tests #
######################

class MockSerializable(core.Serializable):
    TEST_INT = 2

    var1 = core.Boolean()
    var2 = core.Int(default=TEST_INT)
    var3 = core.String(optional=True)
    var4 = core.List(optional=True)

class MockSerializable2(MockSerializable):
    TEST_INT = 1

    var2 = core.Int(default=TEST_INT)
    var5 = core.String(optional=True)

class SerializableTest(unittest.TestCase):
    TEST_INT = 42
    TEST_BOOL = True
    TEST_STR = 'hi'

    def testConstructor_missingRequiredFields(self):
        self.assertRaises(ex.SerializeException, MockSerializable)

    def testConstructor_incorrectRequiredFields(self):
        self.assertRaises(ex.SerializeException, MockSerializable, var1=self.TEST_INT)

    def testConstructor_incorrectOptionalFields(self):
        self.assertRaises(ex.SerializeException, MockSerializable, var1=self.TEST_BOOL,
                          var2=self.TEST_BOOL)

    def testConstructor_unexpectedFields(self):
        self.assertRaises(ex.SerializeException, MockSerializable, var1=self.TEST_BOOL,
                          var2=self.TEST_INT, foo=self.TEST_INT)

    def testConstructor_validArguments(self):
        try:
            MockSerializable(var1=self.TEST_BOOL, var3=self.TEST_STR)
        except ex.SerializeException:
            self.fail("Should not have failed")

    def testConstructor_overrideSuperclassFields(self):
        try:
            obj = MockSerializable2(var1=self.TEST_BOOL)
        except ex.SerializeException:
            self.fail("Should not have failed")

        self.assertEqual(MockSerializable2.TEST_INT, obj.var2)

    def testSetAttr_validType(self):
        obj = MockSerializable(var1=self.TEST_BOOL)
        value = (1, 2, 3)
        obj.var4 = value
        self.assertEqual(list(value), obj.var4)

    def testSetAttr_coercibleType(self):
        obj = MockSerializable(var1=self.TEST_BOOL, var3=self.TEST_STR)
        obj.var1 = not self.TEST_BOOL
        self.assertEqual(not self.TEST_BOOL, obj.var1)

    def testSetAttr_invalidType(self):
        obj = MockSerializable(var1=self.TEST_BOOL, var3=self.TEST_STR)
        try:
            obj.var1 = self.TEST_INT
        except ex.SerializeException:
            pass
        else:
            self.fail("Should have raised a SerializeException")

    def testToJson_noOptional(self):
        obj = MockSerializable(var1=self.TEST_BOOL)
        expect = {'var1': self.TEST_BOOL, 'var2': MockSerializable.TEST_INT}
        self.assertEqual(expect, obj.to_json())

    def testToJson_withOptional(self):
        obj = MockSerializable(var1=self.TEST_BOOL, var3=self.TEST_STR)
        expect = {'var1': self.TEST_BOOL, 'var2': MockSerializable.TEST_INT,
                  'var3': self.TEST_STR}
        self.assertEqual(expect, obj.to_json())

