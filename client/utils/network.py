import logging
import sys

log = logging.getLogger(__name__)

TIMEOUT = 15
SSL_ERROR_MESSAGE = """
ERROR: Your Python installation does not support SSL. You may need to
install OpenSSL and reinstall Python.
""".strip()

def check_ssl():
    """Attempts to import SSL or raises an exception."""
    try:
        import ssl
    except:
        log.warning('Error importing SSL module', stack_info=True)
        print(SSL_ERROR_MESSAGE)
        sys.exit(1)
    else:
        log.info('SSL module is available')
        return ssl
