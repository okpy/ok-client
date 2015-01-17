from client.protocols.common import models
import logging
import os

log = logging.getLogger(__name__)

class BackupProtocol(models.Protocol):
    """The contents of changed source files are sent to the server."""
    name = 'backup'

    def on_start(self):
        """Find all source files and return their complete contents."""
        files = {}
        if self.args.submit:
            # TODO(albert): it seems strange to put this here. Consider moving
            # it elsewhere.
            files['submit'] = True
        for file in self.assignment.src:
            if not os.path.isfile(file):
                # TODO(albert): add an error message
                contents = ''
                log.warning('File {} does not exist'.format(file))
            else:
                with open(file, 'r', encoding='utf-8') as lines:
                    contents = lines.read()
                log.warning('Loaded contents of {} to send to server'.format(file))
            files[file] = contents
        return files

protocol = BackupProtocol
