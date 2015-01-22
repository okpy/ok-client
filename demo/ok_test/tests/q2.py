test = {
  'name': 'Question 2',
  'points': 2,
  'suites': [
    {
      'type': 'concept',
      'cases': [
        {
          'question': 'What is the domain and range of the double function?',
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
      'type': 'doctest',
      'cases': [
        {
          'code': r"""
          >>> double(3)
          6
          """,
        },
        {
          'code': r"""
          >>> double(-4)
          8
          # explanation: doubling a negative number
          """,
        },
      ],
      'setup': r"""
      >>> from hw1 import *
      """,
    }
  ]
}
