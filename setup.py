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
        'requests==2.22.0',
        'certifi==2019.11.28',
        'urllib3==1.25.7',
        'chardet==3.0.4',
        'idna==2.8',
        'coverage==4.4',
        'pytutor==1.0.0',
        'ast-scope==0.3.1',
        'attrs==19.3.0',
        'pyaes==1.6.1',
        'colorama==0.4.3',
        'display-timedelta==1.1',
        'filelock==3.0.12',
    ],
)
