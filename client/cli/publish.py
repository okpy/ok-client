#! /usr/bin/env python3

"""
This module is responsible for publishing ok.
"""

import client
import os
import argparse
import json
import shutil
import zipfile

OK_ROOT = os.path.normpath(os.path.dirname(client.__file__))
STAGING_DIR = os.path.join(os.getcwd(), 'staging')
OK_NAME = 'ok'
CONFIG_NAME = 'config.ok'

REQUIRED_FILES = [
    '__init__',
    'exceptions',
]
REQUIRED_FOLDERS = [
    'utils',
]
COMMAND_LINE = [
    'ok',
]

def populate_staging(staging_dir):
    """Populates the staging directory with files for ok.py."""
    # Command line tools.
    os.mkdir(os.path.join(staging_dir, 'cli'))
    for filename in ['__init__'] + COMMAND_LINE:
        filename += '.py'
        fullname = os.path.join(OK_ROOT, 'cli', filename)
        shutil.copy(fullname, os.path.join(staging_dir, 'cli'))
    shutil.copytree(os.path.join(OK_ROOT, 'cli', 'common'),
                    os.path.join(staging_dir, 'cli', 'common'))

    # Top-level files.
    for filename in REQUIRED_FILES:
        filename += '.py'
        fullname = os.path.join(OK_ROOT, filename)
        shutil.copyfile(fullname, os.path.join(staging_dir, filename))

    for folder in REQUIRED_FOLDERS:
        shutil.copytree(os.path.join(OK_ROOT, folder),
                        os.path.join(staging_dir, folder))

    populate_protocols(staging_dir)
    populate_sources(staging_dir)

def populate_protocols(staging_dir):
    """Populates the protocols/ directory in the staging directory with
    relevant protocols.
    """
    shutil.copytree(os.path.join(OK_ROOT, 'protocols'),
                    os.path.join(staging_dir, 'protocols'))

def populate_sources(staging_dir):
    """Populates the sources/ directory in the staging directory with
    relevant sources.
    """
    shutil.copytree(os.path.join(OK_ROOT, 'sources'),
                    os.path.join(staging_dir, 'sources'))

def create_zip(staging_dir, destination):
    if not os.path.isdir(destination):
        os.mkdir(destination)

    dest = os.path.join(destination, OK_NAME)
    zipf = zipfile.ZipFile(dest, 'w')
    zipf.write(os.path.join(OK_ROOT, '__main__.py'), './__main__.py')
    for root, _, files in os.walk(staging_dir):
        if '__pycache__' in root:
            continue
        for filename in files:
            if filename.endswith('.pyc'):
                continue
            fullname = os.path.join(root, filename)
            # Replace 'staging' with './client' in the zip archive.
            arcname = fullname.replace(staging_dir, './client')
            zipf.write(fullname, arcname=arcname)
    zipf.close()

def new_config():
    """Creates a new config file in the current directory."""
    shutil.copyfile(os.path.join(OK_ROOT, CONFIG_NAME),
                    CONFIG_NAME)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-d', '--destination', type=str, default='.',
                        help='Publish to the specified directory.')
    parser.add_argument('--new-config', action='store_true',
                        help='Creates a new config file in the current directory.')

    return parser.parse_args()

def publish(args):
    if args.new_config:
        new_config()
        exit(0)

    if os.path.exists(STAGING_DIR):
        answer = input('{} already exists. Delete it? [y/n]: '.format(
            STAGING_DIR))
        if answer.lower() in ('yes', 'y'):
            shutil.rmtree(STAGING_DIR)
        else:
            print('Aborting publishing.')
            exit(1)

    os.mkdir(STAGING_DIR)
    try:
        populate_staging(STAGING_DIR)
        create_zip(STAGING_DIR, args.destination)
    finally:
        shutil.rmtree(STAGING_DIR)


def main():
    publish(parse_args())

if __name__ == '__main__':
    main()
