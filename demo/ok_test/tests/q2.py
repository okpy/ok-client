test = {
  'name': 'Question 2',
  'points': 2,
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
          'question': 'What is the domain and range of the double function?'
        }
      ],
      'scored': False,
      'type': 'concept'
    },
    {
      'cases': [
        {
          'code': r"""
          >>> double(3)
          6
          """,
          'hidden': False
        },
        {
          'code': r"""
          >>> double(-4)
          -8
          # explanation: doubling a negative number
          """,
          'hidden': False
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
