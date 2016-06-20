"""Client exceptions."""


class OkException(BaseException):
    """Base exception class for OK."""


class AuthenticationException(OkException):
    """Exceptions related to authentication."""


class ProtocolException(OkException):
    """Exceptions related to protocol errors."""


# TODO(albert): extend from a base class designed for student bugs.
class Timeout(OkException):
    """Exception for timeouts."""
    _message = 'Evaluation timed out!'

    def __init__(self, timeout):
        """Constructor.

        PARAMTERS:
        timeout -- int; number of seconds before timeout error occurred
        """
        super().__init__(self)
        self.timeout = timeout
        self.message = self._message


class LoadingException(OkException):
    """Exception related to loading assignments."""


class SerializeException(LoadingException):
    """Exceptions related to de/serialization."""
