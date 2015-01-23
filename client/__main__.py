import sys

if sys.version_info[0] < 3:
	sys.exit("ok requires Python 3. \nFor more info: http://www-inst.eecs.berkeley.edu/~cs61a/fa14/lab/lab01/#installing-python")

from client.cli import ok

if __name__ == '__main__':
    ok.main()

