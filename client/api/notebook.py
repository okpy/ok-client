import os.path
import time

from client.api.assignment import load_assignment
from client.utils import auth as ok_auth

class Notebook:
    def __init__(self, filepath=None, cmd_args=None):
        self.assignment = load_assignment(filepath, cmd_args)

    def run(self, protocol, messages, **kwargs):
        if protocol not in self.assignment.protocol_map:
            print("{} has not been included in the .ok config".format(protocol))
            return
        return self.assignment.protocol_map[protocol].run(messages, **kwargs)

    def auth(self, force=False, inline=True):
        if not inline:
            ok_auth.authenticate(self.assignment, force=force)
        else:
            ok_auth.notebook_authenticate(self.assignment, force=force)

    def grade(self, *args, **kwargs):
        return self.assignment.grade(*args, **kwargs)

    def grade_all(self, *args, **kwargs):
        for test_key in self.assignment.test_map:
            self.assignment.grade(test_key, *args, **kwargs)

    def score(self, env=None, score_out=None):
        """ Run the scoring protocol.

        score_out -- str; a file name to write the point breakdown
                     into.

        Returns: dict; maps score tag (str) -> points (float)
        """
        messages = {}
        args = ['--score']
        if score_out:
            args.extend(['--score-out', score_out])
        self.assignment.cmd_args.set_args(args)
        if env is None:
            import __main__
            env = __main__.__dict__
        self.run('scoring', messages, env=env)
        return messages['scoring']

    def backup(self):
        messages = {}
        save_notebook()
        time.sleep(2)
        self.assignment.cmd_args.set_args(['--backup'])
        self.run('file_contents', messages)
        return self.run('backup', messages)

    def submit(self):
        messages = {}
        save_notebook()
        self.assignment.cmd_args.set_args(['--submit'])
        self.run('file_contents', messages)
        return self.run('backup', messages)

def save_notebook():
    try:
        from IPython.display import display,Javascript
        display(Javascript('IPython.notebook.save_checkpoint();'))
        display(Javascript('IPython.notebook.save_notebook();'))
    except:
        log.warning("Could not import IPython Save")
        print("Make sure to save your notebook before sending it to OK!")

def wait_for_save(filename, timeout=5):
    """Waits for the file FILENAME to update, waiting up to TIMEOUT seconds.
    Returns True if a save was detected, and False otherwise.
    """
    start_time = time.time()
    modification_time = os.path.getmtime(path)
    while time.time() < start_time + timeout:
        if os.path.getmtime(path) > modification_time:
            return True
        time.sleep(0.1)
    return False
