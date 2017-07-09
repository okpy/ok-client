import shelve # persistance
import hmac # security
import os
from contextlib import contextmanager
from collections.abc import MutableMapping

from client.exceptions import ProtocolException
from client.utils.config import SHELVE_FILE, SECURITY_KEY

__all__ = ['get_store']

##################
# Secure Storage #
##################

TAMPER_MESSAGE = \
"""
Integrity Error: {} was tampered.
Please reverse the changes, or redownload the assignment.
"""

def mac(value):
    mac = hmac.new(SECURITY_KEY)
    mac.update(repr(value).encode('utf-8'))
    return mac.hexdigest()

class SecureStore(MutableMapping):

    def __init__(self, file, prefix):
        self._file = file
        self._prefix = prefix

    @contextmanager
    def open(self):
        with shelve.open(self._file) as db:
            yield db

    def format_key(self, key):
        return os.path.join(self._prefix, key)

    def __getitem__(self, key):
        key = self.format_key(key)
        with self.open() as db:
            data = db[key]
            if not hmac.compare_digest(data['mac'], mac(data['value'])):
                raise ProtocolException(TAMPER_MESSAGE.format(self._file))
            return data['value']

    def __setitem__(self, key, value):
        key = self.format_key(key)
        with self.open() as db:
            db[key] = {'value': value, 'mac': mac(value)}

    def __delitem__(self, key):
        key = self.format_key(key)
        with self.open() as db:
            del db[key]

    def __iter__(self):
        with self.open() as db:
            keys = tuple(db.keys())
        return iter(keys)

    def __len__(self):
        with self.open() as db:
            return len(db)

    def clear(self):
        for key in self:
            if key.startswith(self._prefix):
                with self.open() as db:
                    del db[key]

def get_store(*prefixes):
    prefix = os.path.join(*prefixes)
    return SecureStore(SHELVE_FILE, prefix)


