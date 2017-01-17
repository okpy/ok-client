from client.api.assignment import load_assignment
from client.utils import auth as ok_auth

class Notebook:
    def __init__(self, filepath=None, cmd_args=None):
        self.assignment = load_assignment(filepath, cmd_args)

    def auth(self, force=False, inline=True):
        self.assignment.cmd_args.set_args(['--no-browser'])
        ok_auth.authenticate(self.assignment, force=force)

    def grade(self, *args, **kwargs):
        return self.assignment.grade(*args, **kwargs)

    def backup(self):
        messages = {}
        self.assignment.cmd_args.set_args(['--backup'])
        self.assignment.protocol_map['file_contents'].run(messages)
        return self.assignment.protocol_map['backup'].run(messages)

    def submit(self):
        messages = {}
        self.assignment.cmd_args.set_args(['--submit'])
        self.assignment.protocol_map['file_contents'].run(messages)
        return self.assignment.protocol_map['backup'].run(messages)
