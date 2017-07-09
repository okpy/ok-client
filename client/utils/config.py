import os

CONFIG_DIRECTORY = os.path.join(os.path.expanduser('~'), '.config', 'ok')
CERT_FILE = os.path.join(CONFIG_DIRECTORY, "cacert.pem")
SHELVE_FILE = os.path.join(CONFIG_DIRECTORY, 'storage')
SECURITY_KEY = 'uMWm4sviPK3LyPzgWYFn'.encode('utf-8')

def create_config_directory():
    """
    Setup config directory, which is used for storage of ok-related info,
    like cached access tokens and assignment lock info.

    This method is called when ``client`` module is imported in __init__.py
    """
    if not os.path.exists(CONFIG_DIRECTORY):
        os.makedirs(CONFIG_DIRECTORY)
    return CONFIG_DIRECTORY
