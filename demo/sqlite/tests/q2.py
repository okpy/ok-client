test = {
  'name': 'Question 2',
  'points': 2,
  'suites': [
    {
      'type': 'sqlite',
      'ordered': True,
      'setup': r"""
      sqlite> .open hw1.db
      """,
      'cases': [
        {
          'code': r"""
          sqlite> select * from colors order by color;
          blue|primary
          green|secondary
          red|primary
          yellow|primary
          """,
        },
        {
          'code': r"""
          sqlite> select color from colors order by color;
          blue
          green
          red
          yellow
          """,
        },
      ],
    }
  ]
}
