import sys
import os

VERSION_MESSAGE = """
ERROR: You are using Python {}.{}, but OK requires Python 3.4 or higher.
Make sure you are using the right command (e.g. `python3 ok` instead of
`python ok`) and that you have Python 3 installed.
""".strip()

if sys.version_info[:2] < (3, 4):
    print(VERSION_MESSAGE.format(*sys.version_info[:2]))
    sys.exit(1)

from client.cli import ok

if __name__ == '__main__':
    ok.main()
