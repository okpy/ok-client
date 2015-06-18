test = {
  'name': 'Question 1',
  'points': 3,
  'suites': [
    {
      'type': 'concept',
      'cases': [
        {
          'question': 'What is the domain and range of the square function?',
          'answer': 'Domain is numbers. Range is numbers',
          'choices': [
            'Domain is numbers. Range is numbers',
            'Domain is numbers. Range is strings',
            'Domain is strings. Range is numbers',
            'Domain is strings. Range is strings'
          ],
        }
      ],
    },
    {
      'type': 'wwpp',
      'cases': [
        {
          'code': r"""
          >>> square(3)
          9
          >>> square(5)
          25
          """
        },
        {
          'code': r"""
          >>> print(print(square(4)))
          16
          None
          """
        }
      ],
    },
    {
      'type': 'doctest',
      'cases': [
        {
          'code': r"""
          >>> square(3)
          9
          """,
        },
        {
          'code': r"""
          >>> square(2)
          4
          # explanation: Squaring a negative number
          """,
          'hidden': True,
        },
        {
          'code': r"""
          >>> square(0)
          0
          # explanation: Squaring zero
          """,
          'hidden': True,
        },
        {
          'code': r"""
          >>> 1 / square(0)
          ZeroDivisionError
          """,
          'hidden': True,
        }
      ],
      'setup': r"""
      >>> from hw1 import *
      """,
      'teardown': """
      >>> print('Teardown code')
      """,
    }
  ]
}
