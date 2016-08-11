ok client
=========

The ok client script (written in Python) supports programming projects
by running tests, tracking progress, and assisting in debugging.

Visit [http://okpy.org](http://okpy.org) to use our hosted service for
your course.

The ok client software was developed for CS 61A at UC Berkeley.

[![Build Status](https://travis-ci.org/Cal-CS-61A-Staff/ok-client.svg?branch=master)](https://travis-ci.org/Cal-CS-61A-Staff/ok-client)
[![PyPI Version](http://img.shields.io/pypi/v/okpy.svg)](https://pypi.python.org/pypi/okpy)

## Developer Instructions

### Installation

1. Clone this repo
2. Install [virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/)
3. Create a virtual environment:

        virtualenv -p python3 .
4. Activate the virtual environment:

        source bin/activate
5. Install requirements and set up development environment:

        pip install -r requirements.txt
        python3 setup.py develop

## Contributing

Every time you begin, you should activate the virtual environment:

    source bin/activate

All code for the client is found in the `client/` directory.

There is an executable called `ok` in the virtualenv path that will run your
code locally. You can use the example assignments in the `demo/` directory to
play around:

    cd demo/ok_test
    ok -q q2

The `tests/` directory mirrors the directory structure of the `client/`
directory. Every component of the client should have plenty of tests.
To run all tests, use the following command:

    nosetests tests

## Deployment

To deploy a new version of ok-client, do the following:

1. Change the version number in `client/__init__.py`.
2. Make sure your virtualenv is activated. Also make sure that your `~/.pypirc`
   contains okpy's Pypi credentials.
3. From the base of the repo, make sure your virtualenv is activated and run

        python setup.py sdist upload

4. Make sure to deploy a development version locally:

        python setup.py develop

5. Create an `ok` binary:

        ok-publish

6. Draft a new release on Github with the newly created `ok` binary.
