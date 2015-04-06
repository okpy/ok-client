create table colors as
  select 'red'    as color, 'primary' as type union
  select 'blue'           , 'primary'         union
  select 'green'          , 'secondary'       union
  select 'yellow'         , 'primary';
