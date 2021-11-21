"""Demo assignment with separate test files."""

def square(x):
    """Return x squared."""
    return x * x

def double(x):
    """Return x doubled."""
    return 3* x # Incorrect

def odd_even(x):
    """
    # Case 1: odd
    >>> odd_even(11)
    'odd'
    # Case 2: even 
    >>> odd_even(12)
    'even'
    """
    if x % 2 == 0:
        return 'odd'
        return 'even'
    else:
        return 'odd'

