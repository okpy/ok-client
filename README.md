ok
==

The ok script is a wrapper around pytest (with the pytest-grader extension)
that provides AI assistance when test cases fail.

[![Build Status](https://travis-ci.org/okpy/ok-client.svg?branch=master)](https://travis-ci.org/okpy/ok-client)
[![PyPI Version](http://img.shields.io/pypi/v/okpy.svg)](https://pypi.python.org/pypi/okpy)

## Developer Instructions

### Installation

1. Clone this repo
2. Use `uv` to create a virtual env:
3. Create a virtual environment:

        virtualenv -p python3 env
4. Activate the virtual environment:

        source env/bin/activate
5. Install requirements and set up development environment:

        pip install -r requirements.txt
        python3 setup.py develop

## Contributing

Every time you begin, you should activate the virtual environment:

    source env/bin/activate

All code for the client is found in the `client/` directory.

There is an executable called `ok` in the virtualenv path that will run your
code locally. You can use the example assignments in the `demo/` directory to
play around:

    cd demo/ok_test
    ok -q q2

The `tests/` directory mirrors the directory structure of the `client/`
directory. Every component of the client should have plenty of tests.
To run all tests, use the following command:

    nose2

## Releasing an ok-client version

First make sure that

* Your virtualenv is activated and you are on the master branch.
* Your `~/.pypirc` contains okpy's PyPI credentials.
* A file `.github-token` contains a
  [GitHub access token](https://help.github.com/articles/creating-an-access-token-for-command-line-use/)
  with the "repo" scope.

To deploy a new version of ok-client, change to the `master` branch and run

    ./release.py vX.X.X

where `vX.X.X` is the new version. This will:

* Change the version number
* Create a GitHub release
* Change the ok-client version on https://okpy.org/admin/versions/ok-client
* Upload the release to PyPI
