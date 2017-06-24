from client.protocols.common import models
import logging
import os
from glob import iglob

log = logging.getLogger(__name__)


class FileContentsProtocol(models.Protocol):
    """The contents of source files are sent to the server."""

    def run(self, messages):
        """Find all source files and return their complete contents.

        Source files are considered to be files listed self.assignment.src.
        If a certain source filepath is not a valid file (e.g. does not exist
        or is not a file), then the contents associated with that filepath will
        be an empty string.

        RETURNS:
        dict; a mapping of source filepath -> contents as strings.
        """
        files = {}

        # TODO(albert): move this to AnalyticsProtocol
        if self.args.submit:
            files['submit'] = True

        for src_glob in self.assignment.src:
            num_matches = 0

            for path in iglob(src_glob, recursive=True):
                if not self.is_file(path):
                    contents = ''
                    log.warning('File {} does not exist'.format(path))
                else:
                    contents = self.read_file(path)
                    log.info('Loaded contents of {} to send to server'.format(
                        path))

                files[path] = contents

            if num_matches == 0:
                log.warning('Source glob {} didn\'t match any files'.format(
                    src_glob))

        messages['file_contents'] = files

    #####################
    # Mockable by tests #
    #####################

    def is_file(self, filepath):
        return os.path.isfile(filepath)

    def read_file(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as lines:
            return lines.read()


protocol = FileContentsProtocol
