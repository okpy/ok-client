import shelve # persistance
import hmac # security

##################
# Secure Storage #
##################

SHELVE_FILE = '.ok_storage'
SECURITY_KEY = 'uMWm4sviPK3LyPzgWYFn'.encode('utf-8')

def mac(value):
    mac = hmac.new(SECURITY_KEY)
    mac.update(repr(value).encode('utf-8'))
    return mac.hexdigest()

def contains(root, key):
    key = '{}-{}'.format(root, key)
    with shelve.open(SHELVE_FILE) as db:
        return key in db

def store(root, key, value):
    key = '{}-{}'.format(root, key)
    with shelve.open(SHELVE_FILE) as db:
        db[key] = {'value': value, 'mac': mac(value)}
    return value

def get(root, key, default=None):
    if not contains(root, key):
        return default
    key = '{}-{}'.format(root, key)
    with shelve.open(SHELVE_FILE) as db:
        data = db[key]
        if not hmac.compare_digest(data['mac'], mac(data['value'])):
            raise ProtocolException('{} was tampered.  Reverse changes, or redownload assignment'.format(SHELVE_FILE))
    return data['value']
