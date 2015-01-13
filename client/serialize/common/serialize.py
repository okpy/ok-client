###############
# Field types #
###############

class NoValue(object):
    pass

NoValue = NoValue()

class Field(object):
    _default = NoValue

    def __init__(self, optional=False, **kargs):
        self._optional = optional
        if 'default' in kargs:
            value = kargs['default']
            if not self.is_valid(value):
                raise TypeError('Invalid default: {}'.format(value))
            self._optional = True
            self._default = value

    @property
    def optional(self):
        return self._optional

    @property
    def default(self):
        return self._default

    def is_valid(self, value):
        """Subclasses should override this method for field validation."""
        return True

    def to_json(self, value):
        """Subclasses should override this method for JSON encoding."""
        if not self.is_valid(value):
            raise TypeError('Invalid value: {}'.format(value))
        return value

class Boolean(Field):
    def is_valid(self, value):
        return value in (True, False)

class Int(Field):
    def is_valid(self, value):
        return type(value) == int

class Float(Field):
    def is_valid(self, value):
        return type(value) in (int, float)

class String(Field):
    def is_valid(self, value):
        return type(value) == str

class List(Field):
    def __init__(self, type=None, **kargs):
        """Constructor for a List field.

        PARAMETERS:
        type -- type; if type is None, the List can be heterogeneous.
                Otherwise, the List must be homogeneous with elements
                of the specified type.
        """
        super().__init__(**kargs)
        self._type = type

    def is_valid(self, value):
        valid = type(value) == list
        if self._type is not None:
            valid &= all(isinstance(e, self._type) for e in value)
        return valid

    def to_json(self, value):
        value = super().to_json(value)
        return [elem.to_json() if hasattr(elem, 'to_json') else elem
                             for elem in value]

class Dict(Field):
    def __init__(self, keys=None, values=None, **kargs):
        super().__init__(**kargs)
        self._keys = keys
        self._values = values

    def is_valid(self, value):
        valid = type(value) == dict
        if self._keys is not None:
            valid &= all(isinstance(k, self._keys) for k in value)
        if self._values is not None:
            valid &= all(isinstance(v, self._values) for v in value.values())
        return valid

    def to_json(self, value):
        value = super().to_json(value)
        result = {}
        for k, v in value.items():
            if hasattr(k, 'to_json'):
                k = k.to_json()
            if hasattr(v, 'to_json'):
                v = v.to_json()
            result[k] = v
        return result

########################
# Serializable Objects #
########################

class _SerializeMeta(type):
    def __init__(cls, name, bases, attrs):
        type.__init__(cls, name, bases, attrs)
        cls._fields = {attr: value for attr, value in attrs.items()
                                   if isinstance(value, Field)}
        for base in bases:
            if hasattr(base, '_fields'):
                cls._fields.update(base._fields)

    def __call__(cls, *args, **kargs):
        obj = type.__call__(cls, *args, **kargs)
        # Validate existing arguments
        for attr, value in kargs.items():
            if attr not in cls._fields:
                raise TypeError('__init__() got an unexpected '
                                'keyword argument: {}'.format(attr))
            elif not cls._fields[attr].is_valid(value):
                raise TypeError('__init__() got an invalid argument '
                                '{} for parameter '
                                '{}'.format(value, attr))
            else:
                setattr(obj, attr, value)
        # Check for missing/default fields
        for attr, value in cls._fields.items():
            if attr in kargs:
                continue
            elif value.optional:
                setattr(obj, attr, value.default)
            else:
                raise TypeError('__init__() missing expected '
                                'argument {}'.format(attr))
        obj.post_validate()
        return obj

class Serializable(metaclass=_SerializeMeta):
    def __init__(self, *args, **kargs):
        pass

    def __setattr__(self, attr, value):
        cls = type(self)
        if hasattr(cls, attr):
            field = getattr(cls, attr)
            if value != NoValue and not field.is_valid(value):
                raise TypeError('{}.{} assigned invalid value: '
                                '{}'.format(cls.__name__, attr, value))
        super().__setattr__(attr, value)

    def post_validate(self):
        """Subclasses can override this method to perform post-instantiation
        validation.

        RAISES:
        TypeError; if this instantiation is invalid.
        """
        pass

    def to_json(self):
        cls = type(self)
        json = {}
        for attr, field in cls._fields.items():
            value = getattr(self, attr)
            if not field.optional or value != NoValue:
                json[attr] = field.to_json(value)
        return json

