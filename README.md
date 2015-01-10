ok client
=========

The ok client script (written in Python) supports programming projects
by running tests, tracking progress, and assisting in debugging.

Visit [http://okpy.org](http://okpy.org) to use our hosted service for
your course.

The ok client software was developed for CS 61A at UC Berkeley.

[![Build Status](https://travis-ci.org/Cal-CS-61A-Staff/ok-client.svg?branch=master)](https://travis-ci.org/Cal-CS-61A-Staff/ok-client)

## Developer Instructions

### Installation

1. Clone this repo
2. Install [virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/)
3. Create a virtual environment:

        virtualenv -p python3 .
4. Activate the virtual environment:

        source bin/activate
5. Install requirements:

        pip install -r requirements.txt

## Contributing

Every time you begin, you should activate the virtual environment:

    source bin/activate

All code for the client is found in the `client/` directory.

The `tests/` directory mirrors the directory structure of the `client/`
directory. Every component of the client should have plenty of tests.
To run all tests, use the following command:

    nosetests tests

