This file is for student-created tests. Remember to import the python file(s) 
you wish to test, along with any other modules you may need.
Run tests with "python3 ok -t"

ANNOTATED POOR QUALITY TEST FILE (BUT STILL WORKS)

--------------------------------------------------------------------------------

Suites and cases are run in the order listed in the .rst

Names can be semantic/numeral, and in any order (format: Suite [/d/w]+)

Suite lists

Indentation does not actually matter

							Making comments outside of expected output is fine
>>> master = [1, 2, 3]
>>> more = [4, 5, 6]
	
Case extend

Spacing 
		

		only matters when expecting an output

>>> master.extend(more)

>>> master
[1, 2, 3, 4, 5, 6]

Case pop

>>> a = master.pop()
>>> a
6
Suite algebra

	>>> x = 100
	>>> y = 200
	>>> from hw1 import *
	>>> from hw1_extra import *


	                                                     Case SQUare

		>>> square(x)
		10000
		>>> square(x - 99)
		1

	Case double

		>>> double(y)
		400
		>>> dub = double(double(double(x)))
		>>> dub
		80

Suite alpha
	
>>> why = 'not'
>>> from hw1 import *
>>> from hw1_extra import *

Case zeus

>>> hmmm(why)
'01101000 01101101 01101101 01101101'
>>> inf_loop(10)
'ok'
Case 1

