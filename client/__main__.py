import sys
import os

if sys.version_info[0] < 3:
    sys.exit("ok requires Python 3. \nFor more info: http://www-inst.eecs.berkeley.edu/~cs61a/fa14/lab/lab01/#installing-python")

from client.cli import ok
from client.utils import config
import requests

def patch_requests():
    """ Customize the cacerts.pem file that requests uses.
    Automatically updates the cert file if the contents are different.
    """
    config.create_config_directory()
    ca_certs_file = config.CERT_FILE
    ca_certs_contents = requests.__loader__.get_data('requests/cacert.pem')

    should_write_certs = True

    if os.path.isfile(ca_certs_file):
        with open(ca_certs_file, 'rb') as f:
            existing_certs = f.read()
            if existing_certs != ca_certs_contents:
                should_write_certs = True
                print("Updating local SSL certificates")
            else:
                should_write_certs = False

    if should_write_certs:
        with open(ca_certs_file, 'wb') as f:
            f.write(ca_certs_contents)

    os.environ['REQUESTS_CA_BUNDLE'] = ca_certs_file

patch_requests()

if __name__ == '__main__':
    ok.main()
