
import re

def remove_debug(printed_output):
    return re.sub(r'^DEBUG:.*\n', '', printed_output, flags=re.MULTILINE)
