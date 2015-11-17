test = {
  'name': 'Question 1',
  'points': 2,
  'suites': [
    {
      'type': 'sqlite',
      'ordered': False,
      'setup': r"""
      sqlite> .read hw1.sql
      """,
      'cases': [
        {
          'code': r"""
          sqlite> select * from colors;
          red|primary
          blue|primary
          green|secondary
          yellow|primary
          """,
        },
        {
          'code': r"""
          sqlite> select color from colors;
          red
          blue
          green
          yellow
          """,
        },
      ],
    }
  ]
}
