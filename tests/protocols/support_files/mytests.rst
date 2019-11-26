This file is for student-created tests. Remember to import the python file(s) 
you wish to test, along with any other modules you may need.
Run tests with "python3 ok -t"

IDEAL TEST FILE

--------------------------------------------------------------------------------
Suite lists


	>>> from hw1 import *
	>>> from hw1_extra import *
	>>> master = [1, 2, 3]
	>>> more = [4, 5, 6]
	
	Case extend

		>>> master.extend(more)
		>>> master
		[1, 2, 3, 4, 5, 6]

	Case pop

		>>> a = master.pop()
		>>> a
		6

Suite algebra


	
	>>> from hw1 import *
	>>> from hw1_extra import *

	>>> x = 100
	>>> y = 200

	Case square

		>>> square(x)
		10000
		>>> square(x - 99)
		1
		>>> debugsquare(x)
		10000

	Case double

		>>> double(y)
		400
		>>> dub = double(double(double(x)))
		>>> dub
		800

Suite alpha
	

	>>> from hw1 import *
	>>> from hw1_extra import *
	>>> why = 'not'

	Case zeus

		>>> hmmm(why)
		'01101000 01101101 01101101 01101101'
		>>> inf_loop(10)
		'ok'

	Case 1

		>>> cube(0)
		0
		>>> neverlucky()
		7








