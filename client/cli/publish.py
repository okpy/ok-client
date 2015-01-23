#! /usr/bin/env python3

"""
This module is responsible for publishing ok. This will put all of the
required files (as determined by config.py) into a separate directory
and then make a zipfile called "ok" that can be distributed to students.
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
CONFIG_NAME = 'config.json'

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

def populate_staging(staging_dir, config_path):
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
    # Configuration file.
    shutil.copyfile(config_path, os.path.join(staging_dir, CONFIG_NAME))

    for folder in REQUIRED_FOLDERS:
        shutil.copytree(os.path.join(OK_ROOT, folder),
                        os.path.join(staging_dir, folder))

    config = load_config(config_path)
    populate_protocols(staging_dir, config)
    populate_sources(staging_dir, config)

def load_config(filepath):
    """Loads the configuration file at the given filepath."""
    with open(filepath, 'r') as f:
        return json.load(f)

def populate_protocols(staging_dir, config):
    """Populates the protocols/ directory in the staging directory with
    relevant protocols.
    """
    os.mkdir(os.path.join(staging_dir, 'protocols'))
    shutil.copyfile(os.path.join(OK_ROOT, 'protocols', '__init__.py'),
                    os.path.join(staging_dir, 'protocols', '__init__.py'))
    shutil.copytree(os.path.join(OK_ROOT, 'protocols', 'common'),
                    os.path.join(staging_dir, 'protocols', 'common'))

    for proto in config.get('protocols', []):
        protocol_src = os.path.join(OK_ROOT, 'protocols', proto + '.py')
        protocol_dest = os.path.join(staging_dir, 'protocols', proto + '.py')

        if os.path.isfile(protocol_src):
            shutil.copyfile(protocol_src, protocol_dest)
        else:
            print('Unable to copy protocol {} from {}.'.format(
                proto, protocol_src))

def populate_sources(staging_dir, config):
    """Populates the sources/ directory in the staging directory with
    relevant sources.
    """
    os.mkdir(os.path.join(staging_dir, 'sources'))
    shutil.copyfile(os.path.join(OK_ROOT, 'sources', '__init__.py'),
                    os.path.join(staging_dir, 'sources', '__init__.py'))
    shutil.copytree(os.path.join(OK_ROOT, 'sources', 'common'),
                    os.path.join(staging_dir, 'sources', 'common'))

    for source in set(config.get('tests', {}).values()):
        src = os.path.join(OK_ROOT, 'sources', source)
        dst = os.path.join(staging_dir, 'sources', source)

        if os.path.isfile(src):
            shutil.copyfile(src, dst)
        elif os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            print('Unable to copy source {} from {}.'.format(src, dst))

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

def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-c', '--config', type=str,
                        default=os.path.join(OK_ROOT, CONFIG_NAME),
                        help='Publish with a specificed config file.')
    parser.add_argument('-d', '--destination', type=str, default='.',
                        help='Publish to the specified directory.')

    return parser.parse_args()

def publish(args):
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
        populate_staging(STAGING_DIR, args.config)
        create_zip(STAGING_DIR, args.destination)
    finally:
        shutil.rmtree(STAGING_DIR)


def main():
    publish(parse_args())

if __name__ == '__main__':
    main()
