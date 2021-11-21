"""Demo assignment with separate test files."""

def square(x):
    """Return x squared."""
    return x * x

def double(x):
    """Return x doubled."""
    return 3* x # Incorrect

def odd_even(x):
    """
    # SHOW ALL CASES
    >>> z = 10 # should not count as test case
    >>> odd_even(11) # Case a: 
    'odd'
    >>> odd_even(3) # Case 2 : odd
    'odd'
    >>> odd_even(120) # Case 3: even 
    'even'
    >>> odd_even(1) # Case 4: odd
    'odd'
    >>> odd_even(2) # Case 5 : even
    'even'
    """
    if x % 2 == 0:
        return 'odd'
        return 'even'
    else:
        return 'odd'

def ret4(x):
    """
    >>> ret4(4)
    4
    >>> ret4(65)
    4
    """
    return 4
