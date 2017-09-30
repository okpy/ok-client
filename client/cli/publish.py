"""This module is responsible for publishing OK."""

import argparse
import client
import os
import shutil
import sys
import zipfile

OK_ROOT = os.path.normpath(os.path.dirname(client.__file__))
CONFIG_NAME = 'config.ok'
EXTRA_PACKAGES = ['requests', 'coverage']

def abort(message):
    print(message + ' Aborting', file=sys.stderr)
    sys.exit(1)

def find_site_packages_directory():
    virtualenv = os.getenv('VIRTUAL_ENV')
    if not virtualenv:
        abort('You must activate your virtualenv to publish.')

    for path in sys.path:
        if path.startswith(virtualenv) and 'site-packages' in path:
            return path

    abort('No site packages directory found.')

def write_tree(zipf, src_directory, dst_directory):
    """Write all .py files in a source directory to a destination directory
    inside a zip archive.
    """
    if not os.path.exists(src_directory):
        abort('Tree ' + src_directory + ' does not exist.')
    for root, _, files in os.walk(src_directory):
        for filename in files:
            if not filename.endswith(('.py', '.pem')):
                continue
            fullname = os.path.join(root, filename)
            arcname = fullname.replace(src_directory, dst_directory)
            zipf.write(fullname, arcname=arcname)

def package_client(destination):
    package_dir = find_site_packages_directory()

    if not os.path.isdir(destination):
        os.mkdir(destination)
    dest = os.path.join(destination, client.FILE_NAME)

    with zipfile.ZipFile(dest, 'w') as zipf:
        zipf.write(os.path.join(OK_ROOT, '__main__.py'), '__main__.py')
        write_tree(zipf, OK_ROOT, 'client')
        for package in EXTRA_PACKAGES:
            src_directory = os.path.join(package_dir, package)
            write_tree(zipf, src_directory, package)

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
    else:
        package_client(args.destination)

def main():
    publish(parse_args())

if __name__ == '__main__':
    main()
