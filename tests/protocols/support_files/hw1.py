"""Demo assignment with separate test files."""

def square(x):
    """Return x squared."""
    return x * x

def debugsquare(x):
    """Return x squared but also print a debug value of x."""
    print("DEBUG: the value of x is", x, "in the function debugsquare")
    return x * x

def hmmm(x):
    """Return hmmm."""
    return '01101000 01101101 01101101 01101101'

def double(x):
    """Return x doubled."""
    return x*2

def inf_loop(x):
	while False:
		x = 'Hello'
	return 'ok'
