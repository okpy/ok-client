test = {
  'name': 'Question 1',
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
          scm> (double 3)
          6
          """,
          'hidden': False
        },
        {
          'code': r"""
          scm> (double 4)
          8
          # explanation: doubling a negative number
          """,
          'hidden': False
        }
      ],
      'scored': True,
      'setup': r"""
      scm> (load 'hw1)
      """,
      'teardown': '',
      'type': 'scheme'
    }
  ]
}
