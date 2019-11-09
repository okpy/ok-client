from setuptools import setup, find_packages
import client

VERSION = client.__version__

setup(
    name='okpy',
    version=VERSION,
    author='John Denero, Soumya Basu, Stephen Martinis, Sharad Vikram, Albert Wu',
    # author_email='',
    description=('ok.py supports programming projects by running tests, '
                'tracking progress, and assisting in debugging.'),
    # long_description=long_description,
    url='https://github.com/okpy/ok-client',
    # download_url='https://github.com/okpy/ok/releases/download/v{}/ok'.format(VERSION),

    license='Apache License, Version 2.0',
    keywords=['education', 'autograding'],
    packages=find_packages(include=[
        'client',
        'client.*',
    ]),
    package_data={
        'client': ['config.ok'],
    },
    # install_requires=[],
    entry_points={
        'console_scripts': [
            'ok=client.cli.ok:main',
            'ok-publish=client.cli.publish:main',
            'ok-lock=client.cli.lock:main',
            'ok-test=client.cli.test:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    install_requires=[
        'requests==2.12.4',
        'coverage==4.4'
    ],
)
