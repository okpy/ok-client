test = {
  'name': 'Identity',
  'points': 3,
  'suites': [
    {
      'cases': [
        {
          'code': r"""
          >>> ret3(1)
          3
          >>> ret3(4)
          3
          """,
          'hidden': False,
          'multiline': False
        }
      ],
      'scored': True,
      'setup': r"""
      >>> from fpp.fpp_q1 import *
      """,
      'teardown': '',
      'type': 'doctest'
    }
  ]
}
