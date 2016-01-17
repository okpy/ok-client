"""Demo assignment with separate test files."""

def square(x):
    """
    Return x squared.

    >>> square(3)
    9

    Extra tests:
    >>> square(1)
    1
    >>> square(0)
    0
    >>> square(-4)
    16
    """
    return x * x

def double(x):
    """Return x doubled.

    >>> double(3)
    6
    >>> double(-4)
    -8
    """
    return x # Incorrect

def forever():
    """
    >>> forever()
    1
    """
    while True:
        pass
    return 1
