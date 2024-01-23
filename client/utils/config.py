import os
import glob
import json
import collections

from client import exceptions as ex

CONFIG_DIRECTORY = os.path.join(os.path.expanduser('~'), '.config', 'ok')
REFRESH_FILE = os.path.join(CONFIG_DIRECTORY, "auth_refresh")
CERT_FILE = os.path.join(CONFIG_DIRECTORY, "cacert.pem")

CONFIG_EXTENSION = '*.ok'

def create_config_directory():
    if not os.path.exists(CONFIG_DIRECTORY):
        os.makedirs(CONFIG_DIRECTORY)
    return CONFIG_DIRECTORY

def _get_config(config):
    if config is None:
        configs = glob.glob(CONFIG_EXTENSION)
        if len(configs) > 1:
            raise ex.LoadingException('\n'.join([
                'Multiple .ok files found:',
                '    ' + ' '.join(configs),
                "Please specify a particular assignment's config file with",
                '    python3 ok --config <config file>'
            ]))
        elif not configs:
            raise ex.LoadingException('No .ok configuration file found')
        config = configs[0]
        if config[-3:] != '.ok':
            return {}
    elif not isinstance(config, str):
        return {}
    elif not os.path.isfile(config):
        raise ex.LoadingException(
                'Could not find config file: {}'.format(config))

    try:
        with open(config, 'r') as f:
            result = json.load(f, object_pairs_hook=collections.OrderedDict)
    except IOError:
        raise ex.LoadingException('Error loading config: {}'.format(config))
    except ValueError:
        raise ex.LoadingException(
            '{0} is a malformed .ok configuration file. '
            'Please re-download {0}.'.format(config))
    except FileNotFoundError:
        raise ex.LoadingException(
                'Could not find config file: {}'.format(config))
    else:
        return result
