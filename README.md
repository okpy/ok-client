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
    
## Extensions

Extensions are invoked using a special ok flag.

```
python3 ok --extension [extension]
```

Each extension may have its own set of flags and arguments. Use the
`--extargs` flag to pass these to the extension.

```
python3 ok --extension [extension] --extargs {flag:arg}
```

To create a new extension, create a new python module under the
`client/extensions` directory. The extension must consist of the following,
at the bare minimum:

```
from . import Extension, extension

# all extensions must feature BOTH this decorator AND subclass Extension
@extension
class SampleExt(Extension):
	
	def setup(self, assign=None):
		""" sets up the sample extension """
		print('Setting up sample extension')
		# all args loaded into the self.args dictionary
		if assign and self.args.flag == 'arg':
			# full control over the assignment object
			assign.dump_tests = lambda: 'Tests hidden.'
	    
	def teardown(self, assign):
	    """ run before the test results are dumped """
	    print('Tearing down sample extension')

# required
Extension = SampleExt
```

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