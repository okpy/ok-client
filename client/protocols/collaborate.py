from client.protocols.common import models
from client.utils import format

import logging

log = logging.getLogger(__name__)

class CollaborateProtocol(models.Protocol):

    # Timeouts are specified in seconds.
    SHORT_TIMEOUT = 30
    LONG_TIMEOUT = 30
    API_ENDPOINT = '{prefix}://{server}'
    FIREBASE_CONFIG = {
        'apiKey': "AIzaSyAFJn-q5SbxJnJcPVFhjxd25DA5Jusmd74",
        'authDomain': "ok-server.firebaseapp.com",
        'databaseURL': "https://ok-server.firebaseio.com",
        'storageBucket': "ok-server.appspot.com"
    }

    FILE_TIME_FORMAT = '%m_%d_%H_%M_%S'
    TIME_FORMAT = '%m/%d %H:%M:%S'
    BACKUP_DIRECTORY = 'ok-collab'
    COLLAB_SERVER = 'collab.cs61a.org'

    def run(self, messages):
        if not self.args.collab:
            return

        with format.block("-"):
            print("Collaboration will be available soon.")

protocol = CollaborateProtocol
