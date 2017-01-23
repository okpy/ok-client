import logging
import sys

log = logging.getLogger(__name__)

def explanation_msg(message, short_limit=1, short_msg=None):
    try:
        response = None
        short_responses = 0
        while not response:
            response = input("{}\nYour Response: ".format(message))
            if not response or len(response) < 5:
                response = ''
                short_responses += 1
                log.info("Got a short response. Current count at {}".format(short_responses))
                # Do not ask more than SHORT_LIMIT to avoid annoying the user
                if short_responses > short_limit:
                    break
                if short_msg is None:
                    print("Please enter at least a sentence.")
                else:
                    print(short_msg)
        return response
    except KeyboardInterrupt:
        # Hack for windows
        try:
            print("") # Second I/O will get KeyboardInterrupt
            return 'KeyboardInterrupt'
        except KeyboardInterrupt:
            return 'KeyboardInterrupt'

def confirm(message):
    response = input("{} [yes/no]: ".format(message))
    return response.lower() == "yes" or response.lower() == "y"

