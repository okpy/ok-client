def example(arg1, arg2, arg3):
  """
  Return True iff all the args are truthy and False otherwise.
  >>> example(0, 1, 2)
  0
  >>> example(1, 2, 3)
  3
  >>> example(True, 2, 3)
  3
  """
  # BEGIN SOLUTION CODE
  return arg1 and arg2 and arg3
  # END SOLUTION CODE
