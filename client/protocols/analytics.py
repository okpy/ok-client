"""Implements the AnalyticsProtocol, which keeps track of configuration
for the ok grading session.
"""
import logging
import re

from client.protocols.common import models
from datetime import datetime

# TODO(albert): rename this InformationProtocol
# Add all command line arguments here

log = logging.getLogger(__name__)

class AnalyticsProtocol(models.Protocol):
    """A Protocol that analyzes how much students are using the autograder."""

    RE_SNIPPET = re.compile(r"""
        \s*[\#\;]\s+BEGIN\s+(.*?)\n # \1 is question name
        (.*?)                       # \2 is the contents in between
        \s*[\#\;]\s+END\s+\1\n
        """, re.X | re.I | re.S)

    RE_DEFAULT_CODE = re.compile(r"""
    ^\"\*\*\*\sREPLACE\sTHIS\sLINE\s\*\*\*\"$
    """, re.X | re.I)

    RE_SCHEME_DEFAULT_CODE = re.compile(r"""
    ^\'REPLACE-THIS-LINE$
    """, re.X | re.I)

    RE_REPLACE_MARK = re.compile(r"""
            [\#\;][ ]Replace[ ]
            """, re.X | re.I | re.M)

    def run(self, messages):
        """Returns some analytics about this autograder run."""
        statistics = {}
        statistics['time'] = str(datetime.now())
        statistics['unlock'] = self.args.unlock

        if self.args.question:
            # TODO(denero) Get the canonical name of the question
            statistics['question'] = self.args.question

        statistics['started'] = self.check_start(messages['file_contents'])

        messages['analytics'] = statistics

    def check_start(self, files):
        """returns a dictionary where the key is question name, and the value
        signals whether the question has been started.
        """
        question_status = {}

        for lines in files.values():
            if not isinstance(lines, str):
                continue
            if len(lines) == 0:
                log.warning("File {0} has no content".format(path))

            snippets = self.RE_SNIPPET.findall(lines)

            for snippet in snippets:
                question_name = snippet[0]
                contents = snippet[1] if len(snippet) > 1 else None
                started = True

                if (contents != None
                    and ((self.RE_DEFAULT_CODE.match(contents.strip())
                         or self.RE_SCHEME_DEFAULT_CODE.match(contents.strip()))
                    or (not self.replaced(contents)))):
                    started = False

                if (question_name not in question_status
                    or (not question_status[question_name])):
                    question_status[question_name] = started

        return question_status

    def replaced(self, contents):
        """For a question snippet containing some default code, return True if the
        default code is replaced. Default code in a snippet should have
        '\# Replace with your solution' at the end of each line.
        """
        line_num = len(contents.strip(' ').splitlines())
        replace_marks = self.RE_REPLACE_MARK.findall(contents.strip())
        if len(replace_marks) == line_num:
            return False
        return True


protocol = AnalyticsProtocol
