test = {
  'name': 'Negate',
  'points': 3,
  'suites': [
    {
      'cases': [
        {
          'code': r"""
          >>> negate(1)
          'B'
          """,
          'hidden': False,
          'multiline': False
        }
      ],
      'scored': True,
      'setup': r"""
      >>> from mcq import *
      """,
      'teardown': '',
      'type': 'doctest'
    }
  ]
}
