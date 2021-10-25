test = {
  'name': 'Question MCQ',
  'points': 3,
  'suites': [
    {
      'cases': [
        {
          'code': r"""
          >>> identity(1)
          'B'
          """,
          'hidden': False,
          'multiline': False
        },
        {
          'code': r"""
          >>> negate(-2)
          'A'
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
