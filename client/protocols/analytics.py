"""Implements the AnalyticsProtocol, which keeps track of configuration
for the ok grading session.
"""
import re

from client.protocols.common import models
from datetime import datetime

# TODO(albert): rename this InformationProtocol
# Add all command line arguments here

log = logging.getLogger(__name__)

class AnalyticsProtocol(models.Protocol):
    """A Protocol that analyzes how much students are using the autograder."""

    def run(self, messages):
        """Returns some analytics about this autograder run."""
        statistics = {}
        statistics['time'] = str(datetime.now())
        statistics['unlock'] = self.args.unlock

        if self.args.question:
            # TODO(denero) Get the canonical name of the question
            statistics['question'] = self.args.question

        # TODO(Jack) start from here: for adding the file analysis
        statistics['started'] = self.analyze_file(messages['file_contents'])

        messages['analytics'] = statistics

    def analyze_file(self, files):
        """returns a dictionary where the key is question number, and the value
        signals whether the question has been started.
        """
        begin = re.compile(r"""
            [ \t]*
            \#[ ]BEGIN[ ](.+)    # \1 is the question tag
            """, re.X | re.M)
        end = re.compile(r"""
            [ \t]*
            \#[ ]END[ ](.+)    # \1 is the question tag
            """, re.X | re.M)
        replace = re.compile(r"""
            \#[ ]Replace[ ].+
            """, re.X | re.M)

        q_status = {}

        # tags = [i for i in range(len(lines)) if
        #     begin.match(lines[i]) or end.match(lines[i])]
        #
        # if len(tag)
        for path in files:
            lines = files[path].splitlines()
            if len(lines) == 0:
                log.warning("File {0} has no content".format(path))
            line_num = 0
            started = False
            in_block = False
            prev_q_tag = None
            while line_num < len(lines):
                line = lines[line_num]
                begin_match = begin.match(line)
                end_match = end.match(line)
                if begin_match:
                    q_tag = begin_match.group(1)
                    prev_q_tag = q_tag
                    started = True
                    if not in_block:
                        in_block = True
                    else:
                        # write current q_tag, started to dictionary
                        if not (q_tag in q_status and q_status[q_tag]):
                            q_status[q_tag] = started
                        started = True
                        in_block = True
                elif end_match:
                    q_tag = end_match.group(1)
                    if not (q_tag in q_status and q_status[q_tag]):
                        if q_tag == prev_q_tag:
                            q_status[q_tag] = started
                        else:
                            q_status[q_tag] = True
                    started = False
                    in_block = False
                    prev_q_tag = None
                else:
                    if in_block:
                        if not replace.search(line) or not line.strip():
                            started = True
                line_num += 1
            return q_status
