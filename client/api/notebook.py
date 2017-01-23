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
        self.save_notebook()
        time.sleep(2)
        self.assignment.cmd_args.set_args(['--backup'])
        self.run('file_contents', messages)
        return self.run('backup', messages)

    def submit(self):
        messages = {}
        self.save_notebook()
        self.assignment.cmd_args.set_args(['--submit'])
        self.run('file_contents', messages)
        return self.run('backup', messages)

    def save_notebook(self):
        try:
            from IPython.display import display,Javascript
            display(Javascript('IPython.notebook.save_checkpoint();'))
            display(Javascript('IPython.notebook.save_notebook();'))
            ipynbs = [path in self.assignment.src
                if os.path.splitext(path)[1] == '.ipynb']
            if not wait_for_save(ipynbs):
                log.warning("Timed out waiting for IPython save")
                print("Could not save your notebook. Make sure your notebook is saved before sending it to OK!")
        except:
            log.warning("Could not import IPython Save")
            print("Make sure to save your notebook before sending it to OK!")

def wait_for_save(filenames, timeout=5):
    """Waits for one of the files in the list FILENAMES to update, waiting up to
    TIMEOUT seconds. Returns True if a save was detected, and False otherwise.
    """
    start_time = time.time()
    while time.time() < start_time + timeout:
        if any(os.path.getmtime(path) > start_time for path in filenames):
            return True
        time.sleep(0.1)
    return False
