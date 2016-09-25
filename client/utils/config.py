import os
import pickle

CONFIG_DIRECTORY = os.path.join(os.path.expanduser('~'), '.config', 'ok')
REFRESH_FILE = os.path.join(CONFIG_DIRECTORY, "auth_refresh")
CERT_FILE = os.path.join(CONFIG_DIRECTORY, "cacert.pem")

def create_config_directory():
    if not os.path.exists(CONFIG_DIRECTORY):
        os.makedirs(CONFIG_DIRECTORY)
    return CONFIG_DIRECTORY

def get_storage():
    create_config_directory()
    with open(REFRESH_FILE, 'rb') as fp:
        storage = pickle.load(fp)

    access_token = storage['access_token']
    expires_at = storage['expires_at']
    refresh_token = storage['refresh_token']

    return access_token, expires_at, refresh_token