#!/usr/bin/env python3
from distutils.version import StrictVersion
import os
import re
import requests
import subprocess
import sys
import tempfile

from client.api import assignment
from client.utils import auth

GITHUB_TOKEN_FILE = '.github-token'
GITHUB_REPO = 'okpy/ok-client'
OK_SERVER_URL = 'okpy.org'

def abort(message=None):
    if message:
        print('ERROR:', message, file=sys.stderr)
    sys.exit(1)

def shell(command, capture_output=False):
    kwargs = dict(shell=True, check=True)
    if capture_output:
        kwargs.update(stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    else:
        print('>', command)
    try:
        output = subprocess.run(command, **kwargs)
    except subprocess.CalledProcessError as e:
        print(str(e), file=sys.stderr)
        if capture_output:
            print(e.stderr.decode('utf-8'), file=sys.stderr)
        abort()
    if capture_output:
        return output.stdout.decode('utf-8').strip()

def edit(text):
    # from Mercurial sources:
    # https://selenic.com/repo/hg-stable/file/2770d03ae49f/mercurial/ui.py#l318
    (fd, name) = tempfile.mkstemp(
        prefix='ok-client-release-', suffix='.txt', text=True)
    try:
        f = os.fdopen(fd, 'w')
        f.write(text)
        f.close()

        editor = os.environ.get('EDITOR', 'vi')
        shell('{} \"{}\"'.format(editor, name))
        f = open(name)
        t = f.read()
        f.close()
    finally:
        os.unlink(name)
    return t

def post_request(url, *args, **kwargs):
    try:
        print('POST', url)
        r = requests.post(url, *args, **kwargs)
        r.raise_for_status()
    except Exception as e:
        abort(str(e))
    return r.json()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: {} NEW_VERSION'.format(sys.argv[0]), file=sys.stderr)
        abort()
    new_release = sys.argv[1]

    # change to directory that script is in; should be root of project
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    # read GitHub token
    try:
        with open(GITHUB_TOKEN_FILE, 'r') as f:
            github_token = f.read().strip()
    except (OSError, IOError) as e:
        print('No GitHub access token found.', file=sys.stderr)
        print('Generate an access token with the "repo" scope as per', file=sys.stderr)
        print('https://help.github.com/articles/creating-an-access-token-for-command-line-use/', file=sys.stderr)
        print('and paste the token into a file named "{}".'.format(GITHUB_TOKEN_FILE), file=sys.stderr)
        abort()

    if new_release[:1] != 'v':
        abort("Version must start with 'v'")
    if shell('git rev-parse --abbrev-ref HEAD', capture_output=True) != 'master':
        abort('You must be on master to release a new version')
    shell('git pull --ff-only --tags')

    # find latest release
    latest_release = shell('git describe --tags --abbrev=0', capture_output=True)
    latest_release_commit = shell('git rev-list -n 1 {}'.format(latest_release),
        capture_output=True)

    print('Latest version: {} ({})'.format(latest_release, latest_release_commit[:7]))
    print('New version: {}'.format(new_release))

    # uninstall ``okpy`` in virtual env, if installed
    shell('pip uninstall okpy')

    # run tests
    shell('nosetests tests')

    # check that release numbers are sane
    try:
        latest_version = StrictVersion(latest_release[1:])
        new_version = StrictVersion(new_release[1:])
    except ValueError as e:
        abort(str(e))
    if latest_version >= new_version:
        abort('Version numbers must be increasing')
    elif new_version.version[0] > latest_version.version[0] + 1:
        abort('Major version number cannot increase by more than one')

    # edit changelog message
    log = shell('git log --pretty=format:"- %s" {}..HEAD'.format(latest_release),
        capture_output=True)
    changelog = edit('\n'.join([
        'Changelog:',
        log,
        '',
        '# Please enter a changelog since the latest release. Lines starting',
        "# with '#' will be ignored, and an empty message aborts the release.",
    ]))
    log_lines = [line for line in changelog.splitlines() if line[:1] != '#']
    changelog = '\n'.join(log_lines).strip()
    if not changelog:
        abort('Empty changelog, aborting')

    # edit client/__init__.py and commit
    init_file = 'client/__init__.py'
    with open(init_file, 'r', encoding='utf-8') as f:
        old_init = f.read()
    new_init = re.sub(
        r"^__version__ = '([a-zA-Z0-9.]+)'",
        "__version__ = '{}'".format(new_release),
        old_init)
    if old_init != new_init:
        print('Editing version string in {}'.format(init_file))
        with open(init_file, 'w', encoding='utf-8') as f:
            init = f.write(new_init)
        shell('git add {}'.format(init_file))
        shell('git commit -m "Bump version to {}"'.format(new_release))
        shell('git push')

    print('Uploading release to GitHub...')
    shell('python setup.py develop')
    shell('ok-publish')
    github_release = post_request(
        'https://api.github.com/repos/{}/releases'.format(GITHUB_REPO),
        headers={
            'Authorization': 'token ' + github_token,
        },
        json={
            'tag_name': new_release,
            'target_commitish': 'master',
            'name': new_release,
            'body': changelog,
            'draft': False,
            'prerelease': False
        },
    )
    with open('ok', 'rb') as f:
        github_asset = post_request(
            'https://uploads.github.com/repos/{}/releases/{}/assets'.format(
                GITHUB_REPO, github_release['id']),
            params={
                'name': 'ok'
            },
            headers={
                'Authorization': 'token ' + github_token,
                'Content-Type': 'application/octet-stream',
            },
            data=f,
        )

    print('Updating version on {}...'.format(OK_SERVER_URL))
    args = assignment.Settings(server=OK_SERVER_URL)
    access_token = auth.authenticate(args, force=True)
    post_request('https://{}/api/v3/version/ok-client'.format(OK_SERVER_URL),
        headers={
            'Authorization': 'Bearer ' + access_token,
        },
        json={
            'current_version': new_release,
            'download_link': github_asset['browser_download_url'],
        },
    )

    print('Uploading release to PyPI...')
    shell('python setup.py sdist bdist_wheel upload')

    print()
    print('Released okpy=={}'.format(new_release))
    print('Remember to update the requirements.txt file for any repos that depend on okpy.')
