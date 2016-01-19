test = {
  'name': 'Question 3',
  'points': 2,
  'suites': [
    {
      'type': 'sqlite',
      'ordered': False,
      'setup': r"""
      """,
      'cases': [
        {
          'code': r"""
          sqlite> with
             ...>   ints(n) as (
             ...>   select 1 union
             ...>   select n+1 from ints
             ...>  )
             ...> select n from ints order by n;
          1
          """,
        },
      ],
    }
  ]
}
