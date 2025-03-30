class Protocol(object):
    """A Protocol encapsulates a single aspect of OK functionality."""

    def __init__(self, args, assignment):
        """Constructor.

        PARAMETERS:
        args       -- Namespace; parsed command line arguments by argparse.
        assignment -- dict; general information about the assignment.
        """
        self.args = args
        self.assignment = assignment

    def run(self, messages):
        """Executes the protocol, given a dictionary of messages.

        PARAMETERS:
        messages -- dict; a structure that Protocols can use to record data
                    and/or send to a server.
        """
        raise NotImplementedError

import os
import pickle
import hmac
class ResearchProtocol(Protocol):
    """Helper attributes and methods for 61A-bot research project with larynqi@, zamfi@, norouzi@, denero@"""

    SERVER = 'https://61a-bot-backend.zamfi.net'
    SERVER_KEY = 'jfv97pd8ogybhilq3;orfuwyhiulae'
    CS61A_ENDPOINT = 'cs61a'
    C88C_ENDPOINT = 'c88c'
    CS61A_ID = '61a'
    C88C_ID = '88c'
    UNKNOWN_COURSE = '<unknown course>'

    GET_CONSENT = True
    CONSENT_CACHE = '.ok_consent'
    NO_CONSENT_OPTIONS = {"n", "no", "0", "-1", }
    CONSENT_MESSAGE = "Can we collect your de-identified data for research directed by Prof. Narges Norouzi (EECS faculty member unaffiliated with this course)? Your consent is voluntary and does not affect your ability to use this tool or your course grade. For more information visit https://cs61a.org/articles/61a-bot\n\nYou can change your response at any time by running `python3 ok --consent`."

    def _mac(self, key, value):
        mac = hmac.new(key.encode('utf-8'), digestmod='sha512')
        mac.update(repr(value).encode('utf-8'))
        return mac.hexdigest()
        
    def _get_consent(self, email):
        if self.GET_CONSENT:
            if self.CONSENT_CACHE in os.listdir() and not self.args.consent:
                try:
                    with open(self.CONSENT_CACHE, 'rb') as f:
                        data = pickle.load(f)
                        if not hmac.compare_digest(data.get('mac'), self._mac(email, data.get('consent'))):
                            os.remove(self.CONSENT_CACHE)
                            return self._get_consent(email)
                    return data.get('consent')
                except:
                    os.remove(self.CONSENT_CACHE)
                    return self._get_consent(email)
            else:
                print(self.CONSENT_MESSAGE)
                res = input("\n(Y/n)? ").lower()
                consent = res not in self.NO_CONSENT_OPTIONS
                if consent:
                    print("\nYou have consented.\n")
                else:
                    print("\nYou have not consented.\n")
                with open(self.CONSENT_CACHE, 'wb') as f:
                    pickle.dump({'consent': consent, 'mac': self._mac(email, consent)}, f, protocol=pickle.HIGHEST_PROTOCOL)
                return consent
        else:
            return False
    
    def _check_solved(self, messages):
        tests = self.assignment.specified_tests
        grading_analytics = messages.get('grading', {})
        active_function = tests[-1].name
        for test in tests:
            name = test.name
            if name in grading_analytics and grading_analytics[name]['failed'] > 0:
                return {
                    'failed': True,
                    'active_function': name
                }
        return {
            'failed': False,
            'active_function': active_function
        }
