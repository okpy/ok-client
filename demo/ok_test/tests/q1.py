test = {
  'name': 'Question 1',
  'points': 3,
  'suites': [
    {
      'cases': [
        {
          'answer': 'Domain is numbers. Range is numbers',
          'choices': [
            'Domain is numbers. Range is numbers',
            'Domain is numbers. Range is strings',
            'Domain is strings. Range is numbers',
            'Domain is strings. Range is strings'
          ],
          'hidden': False,
          'multiline': False,
          'question': 'What is the domain and range of the square function?'
        }
      ],
      'scored': False,
      'type': 'concept'
    },
    {
      'cases': [
        {
          'code': r"""
          >>> square(3)
          9
          >>> square(5)
          25
          """,
          'hidden': False,
          'multiline': False
        },
        {
          'code': r"""
          >>> print(print(square(4)))
          16
          None
          """,
          'hidden': False,
          'multiline': False
        }
      ],
      'scored': False,
      'type': 'wwpp'
    },
    {
      'cases': [
        {
          'code': r"""
          >>> square(3)
          9
          """,
          'hidden': False,
          'multiline': False
        },
        {
          'code': r"""
          >>> square(2)
          4
          # explanation: Squaring a negative number
          """,
          'hidden': True,
          'multiline': False
        },
        {
          'code': r"""
          >>> square(0)
          0
          # explanation: Squaring zero
          """,
          'hidden': True,
          'multiline': False
        },
        {
          'code': r"""
          >>> 1 / square(0)
          ZeroDivisionError
          >>> square(1) / square(0)
          Traceback (most recent call last):
            ...
          ZeroDivisionError: division by zero
          """,
          'hidden': True,
          'multiline': False
        }
      ],
      'scored': True,
      'setup': r"""
      >>> from hw1 import *
      """,
      'teardown': r"""
      >>> print('Teardown code')
      """,
      'type': 'doctest'
    }
  ]
}
