from client.protocols.common import models
from client.utils import auth

import logging

log = logging.getLogger(__name__)

class AutoStyleProtocol(models.Protocol):
    def run(self, messages):
        if not self.args.style:
            log.info("Autostyle not enabled.")
            return
        elif self.args.local:
            log.info("Autostyle requires network access.")
            return

        if not messages.get('analytics'):
            log.warning("Autostyle needs to be after analytics")
            return

        messages['analytics']['autostyle'] = 'not ready'

        print("Autostyle is not enabled yet. Check back soon")

protocol = AutoStyleProtocol
