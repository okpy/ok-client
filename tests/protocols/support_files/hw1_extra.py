"""Demo assignment with separate test files."""
from random import randint

def cube(x):
    """Return x cubed."""
    return x * x *x

def neverlucky():
    """Return magic."""
    randint(0, 9)
    return 'magic'
