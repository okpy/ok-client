from client import exceptions

class Protocol(object):
    """A Protocol encapsulates a single aspect of ok.py functionality."""
    def __init__(self, cmd_line_args, assignment):
        """Constructor.

        PARAMETERS:
        cmd_line_args -- Namespace; parsed command line arguments.
                         command line, as parsed by argparse.
        assignment    -- dict; general information about the assignment.
        """
        self.args = cmd_line_args
        self.assignment = assignment

    def on_start(self):
        """Called when ok.py starts. Returns an object to be sent to server."""

    def on_interact(self):
        """Called to execute an interactive or output-intensive session."""

