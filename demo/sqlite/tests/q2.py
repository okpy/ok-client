test = {
  'name': 'Question 2',
  'points': 2,
  'suites': [
    {
      'type': 'sqlite',
      'setup': r"""
      sqlite> .open hw1.db
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
