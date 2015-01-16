from client.protocols.common import models

def normalize(text):
    """Normalizes whitespace in a specified string of text."""
    return " ".join(text.split())

class LockProtocol(models.Protocol):
    """Locking protocol that wraps that mechanism."""

    name = 'lock'

    def on_start(self):
        """Responsible for locking each test."""
        if self.args.lock:
            formatting.print_title('Locking tests for {}'.format(
                self.assignment['name']))

            if self.assignment['hidden_params']:
                self.assignment['hidden_params'] = {}
                print('* Removed hidden params for assignment')

            for test in self.assignment.tests:
                lock(test, self._hash_fn)
            print('Completed locking {}.'.format(self.assignment['name']))
            print()

    @property
    def _alphabet(self):
        return string.ascii_lowercase + string.digits

    def _hash_fn(self, text):
        text = normalize(text)
        return hmac.new(self.assignment['name'].encode('utf-8'),
                        text.encode('utf-8')).hexdigest()

def lock(test, hash_fn):
    formatting.underline('Locking Test ' + test.name, line='-')

    if test['hidden_params']:
        test['hidden_params'] = {}
        print('* Removed hidden params')

    num_cases = 0
    for suite in test['suites']:
        for case in list(suite):
            num_cases += 1  # 1-indexed
            if case['hidden']:
                suite.remove(case)
                print('* Case {}: removed hidden test'.format(num_cases))
            elif not case['never_lock'] and not case['locked']:
                case.on_lock(hash_fn)
                print('* Case {}: locked test'.format(num_cases))
            elif case['never_lock']:
                print('* Case {}: never lock'.format(num_cases))
            elif case['locked']:
                print('* Case {}: already locked'.format(num_cases))

protocol = LockProtocol
