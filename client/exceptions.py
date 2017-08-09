"""Client exceptions."""

import client

import sys
import logging

log = logging.getLogger(__name__)   # Get top-level logger

class OkException(Exception):
    """Base exception class for OK."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        log.debug('Exception raised: {}'.format(type(self).__name__))
        log.debug('python version: {}'.format(sys.version_info))
        log.debug('okpy version: {}'.format(client.__version__))



class AuthenticationException(OkException):
    """Exceptions related to authentication."""


class OAuthException(AuthenticationException):
    def __init__(self, error='', error_description=''):
        super().__init__()
        self.error = error
        self.error_description = error_description


class ProtocolException(OkException):
    """Exceptions related to protocol errors."""


class EarlyExit(OkException):
    """Exceptions related to early exits that are NOT errors."""


# TODO(albert): extend from a base class designed for student bugs.
class Timeout(OkException):
    """Exception for timeouts."""
    _message = 'Evaluation timed out!'

    def __init__(self, timeout):
        """Constructor.

        PARAMTERS:
        timeout -- int; number of seconds before timeout error occurred
        """
        super().__init__()
        self.timeout = timeout
        self.message = self._message


class LoadingException(OkException):
    """Exception related to loading assignments."""


class SerializeException(LoadingException):
    """Exceptions related to de/serialization."""
