test = {
  'name': 'Test',
  'points': 0,
  'suites': [
    {
      'cases': [
        {
          'code': r"""
          >>> 1 + 1 # OK will accept 'black' as right answer
          e74918d4310bb6cbc896676f20dc20de
          # locked
          >>> 2 + 2 # OK will accept 'black' as right answer
          e74918d4310bb6cbc896676f20dc20de
          # locked
          """,
          'hidden': False,
          'locked': True
        }
      ],
      'scored': False,
      'type': 'wwpp'
    }
  ]
}