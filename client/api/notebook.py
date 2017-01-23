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
        if inline:
            self.assignment.cmd_args.set_args(['--no-browser'])
        ok_auth.authenticate(self.assignment, force=force)

    def grade(self, *args, **kwargs):
        return self.assignment.grade(*args, **kwargs)

    def score(self, env=None):
        messages = {}
        self.assignment.cmd_args.set_args(['--score'])
        if env is None:
            import __main__
            env = __main__.__dict__
        self.run('scoring', messages, env=env)
        return messages

    def backup(self):
        messages = {}
        self.assignment.cmd_args.set_args(['--backup'])
        self.run('file_contents', messages)
        return self.run('backup', messages)

    def submit(self):
        messages = {}
        self.assignment.cmd_args.set_args(['--submit'])
        self.run('file_contents', messages)
        return self.run('backup', messages)
