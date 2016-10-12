from client.protocols.common import models
from client.utils import auth
from client.utils import network
from datetime import datetime
from urllib import error
import logging
import os
import shutil

log = logging.getLogger(__name__)

GAE_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

DEFAULT_BACKUP_DIR = "ok-backup"

class RestoreProtocol(models.Protocol):
    """Restores an assignment from an earlier backup."""

    def run(self, messages):
        """If the --restore flag is present, allow users to select
        a backup to restore from.
        """
        if not self.args.restore:
            return
        
        if self.args.local:
            print("Cannot restore when running ok with --local.")
            return

        self.access_token = auth.authenticate(self.args.authenticate)
        
        print('Loading backups...')
        
        response = self.request('user')
        if not response:
            print('Could not connect to server.')
            return
        user = response['data']['results'][0]
        email = user['email'][0]
        assign_id = self.get_assign_id(self.assignment.endpoint)
        backups = self.get_backups(email, assign_id)
        current_time = datetime.now()
        print('0: Cancel Restore')
        for current in range(0, len(backups)):
            backup = backups[current]
            time_diff = get_time_diff(backup['timestamp'], current_time)
            print('{0}: {1} by {2}'.format(current + 1, time_diff, backup['submitter']))
        response = input('Backup #: ')
        selection = int(response) - 1
        if selection < 0 or selection >= len(backups):
            print("Invalid option for restoring backups.")
            return
        self.restore_backup(backups[selection])
        
    def restore_backup(self, backup):
        contents = backup['file_contents']
        backup_dir = find_backup_dir()
        os.makedirs(backup_dir)
        for filename in contents:
            if filename != 'submit':
                if os.path.exists(filename):
                    shutil.copyfile(filename, os.path.join(backup_dir, filename))
                with open(filename, "w+") as f:
                    f.write(contents[filename])
                    f.flush()
                    os.fsync(f.fileno())
        print("Restore complete.")
        print("Existing local files have been moved to '{0}'".format(backup_dir))
        
    def get_backups(self, email, assign_id):
        params = {
            'assignment': assign_id
        }
        response = self.request('user/{0}/get_backups'.format(email), params)
        backups = []
        for backup in response['data']:
            if 'file_contents' in backup['messages']:
                backups.append({
                    'file_contents': backup['messages']['file_contents'],
                    'submitter': backup['submitter']['email'][0],
                    'timestamp': datetime.strptime(backup['created'], GAE_DATETIME_FORMAT)
                })
        return backups
       
    def get_assign_id(self, endpoint):
        """Gets the assignment id for the given endpoint"""
        response = self.request('assignment')
        for assign in response['data']['results']:
            if assign['name'] == endpoint:
                return assign['id']
                
    def request(self, route, params={}):
        """Makes an API request"""
        return network.api_request(self.access_token, self.args.server, 
            route, self.args.insecure, params)
            
def get_time_diff(start, end):
    diff = end - start
    seconds = int(diff.total_seconds())
    minutes = seconds // 60
    hours = seconds // 3600
    days = seconds // 86400
    if seconds < 60:
        return '{0} seconds ago'.format(seconds)
    elif seconds < 3600:
        return '{0} minutes, {1} seconds ago'.format(minutes, seconds % 60)
    elif seconds < 86400:
        return '{0} hours, {1} minutes ago'.format(hours, minutes % 60)
    return '{0} days, {1} hours ago'.format(days, hours % 23)
    
def find_backup_dir():
    if not os.path.exists(DEFAULT_BACKUP_DIR):
        return DEFAULT_BACKUP_DIR
    counter = 1
    while os.path.exists(DEFAULT_BACKUP_DIR + str(counter)):
        counter += 1
    return DEFAULT_BACKUP_DIR + str(counter)

protocol = RestoreProtocol
