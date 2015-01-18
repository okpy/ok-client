test = {
  'extra': False,
  'name': 'Question 1',
  'points': 3,
  'suites': [
    {
      'cases': [
        {
          'answer': '1',
          'choices': [
            'Domain is numbers. Range is numbers',
            'Domain is numbers. Range is strings',
            'Domain is strings. Range is numbers',
            'Domain is strings. Range is strings'
          ],
          'hidden': False,
          'locked': False,
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
          """,
          'hidden': False,
          'locked': False
        },
        {
          'code': r"""
          >>> square(-2)
          4
          # explanation: Squaring a negative number
          """,
          'hidden': False,
          'locked': False
        },
        {
          'code': r"""
          >>> square(0)
          0
          # explanation: Squaring zero
          """,
          'hidden': False,
          'locked': False
        },
        {
          'code': r"""
          >>> sd
          NameError
          """,
          'hidden': False,
          'locked': False
        }
      ],
      'scored': True,
      'setup': r"""
      >>> from hw1 import *
      """,
      'teardown': '',
      'type': 'doctest'
    }
  ]
}