from client.protocols.common import models
import os


class FileContents(models.Protocol):
    """The contents of changed source files are sent to the server."""
    name = 'file_contents'

    def on_start(self):
        """Find all source files and return their complete contents."""
        contents = {}
        if self.args.submit:
            contents['submit'] = True
        for path in self.assignment['src_files']:
            key = os.path.normpath(os.path.split(path)[1])
            with open(path, 'r', encoding='utf-8') as lines:
                value = lines.read()
            contents[key] = value
        return contents

protocol = FileContents
