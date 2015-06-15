class Messages(dict):
    """A subclass of dictionary that prints a warning when an existing is
    overwritten.
    """
    def __setitem__(self, key, value):
        if key in self:
            print('Warning: Overwriting key {}. '
                  'Old: {}; New: {}'.format(key, self[key], value))
        super().__setitem__(key, value)
