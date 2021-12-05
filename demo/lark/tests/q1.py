test = {
  'name': 'Question 1',
  'points': 2,
  'suites': [
    {
      'cases': [
        {
          'code': r"""
          lark> (+ 1 (+ 2 3))
          start
            calc_op
              +
              1
              calc_op
                +
                2
                3
          """,
          'hidden': False,
          'multiline': False
        }
      ],
      'scored': True,
      'setup': r"""
      %import hw1 (calc_expr, calc_op)
      %ignore /\s+/
      start: calc_expr
      """,
      'teardown': '',
      'type': 'lark'
    }
  ]
}
