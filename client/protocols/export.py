from client.protocols.common import models
from client.utils import auth
from client.utils import network
from datetime import datetime
from urllib import error
import client
import logging
import os
import pickle

log = logging.getLogger(__name__)

GAE_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

class ExportProtocol(models.Protocol):
    """Downloads submissions from the server"""

    def run(self, messages):
        """If the --export parameter was used, downloads all submissions 
        for the current assignment from the server and then exits
        """
        data = None
        try:
            data = pickle.load(open("export_cache.pkl", "rb"))
            self.access_token = auth.authenticate(self.args.authenticate)
            log.info('Authenticated with access token %s', self.access_token)
        except IOError:
            if self.args.export:
                self.access_token = auth.authenticate(self.args.authenticate)
                log.info('Authenticated with access token %s', self.access_token)
                data = {
                    'endpoint': self.assignment.endpoint   
                }
                data['assign'], data['course'] = self.get_ids(data['endpoint'])
                data['students'] = self.get_students(data['course'])
                if not data['students']:
                    return
                data['current'] = 0
        
        if data:
            i = 0
            try:
                if not os.path.exists('submissions'): 
                    os.makedirs('submissions')
                
                downloads_left = len(data['students']) - data['current']
                
                print("{0} submissions left to download".format(downloads_left))
                
                for i in range(data['current'], len(data['students'])):
                    student = data['students'][i]
                    try:
                        self.download_submission(student, data['assign'])
                        data['current'] = i + 1
                    except (IOError, error.HTTPError):
                        data['current'] = i
                        pickle.dump(data, open("export_cache.pkl", "wb"))
                        dl_left = len(data['students']) - i
                        print("Download failed. Run command again to continue.")
                        print("Progress is saved in export_cache.pkl")
                        print("{0} submissions left to download".format(dl_left))
                        return
                        
            except KeyboardInterrupt:
                pickle.dump(data, open("export_cache.pkl", "wb"))
                dl_left = len(data['students']) - i
                print("Download interrupted. Run command again to continue.")
                print("{0} submissions left to download".format(dl_left))
                return
                
            print("Submissions downloaded.")
            if os.path.exists('export_cache.pkl'):
                os.remove('export_cache.pkl')
        
    def download_submission(self, student, assign_id):
        """Downloads a student's final submission for an assignment"""
        params = {'assignment': assign_id}
        response = self.request('user/{0}/final_submission'.format(student[0]),
            params)
        if not response['data']:
            print("No final submission for {0}".format(student[0]))
            return
        raw_data = response['data']
        contents = raw_data['submission']['backup']['messages']['file_contents']
        timestamp = datetime.strptime(raw_data['submission']['backup']['server_time'], GAE_DATETIME_FORMAT)
        subm_id = raw_data['submission']['backup']['id']
        subm_dir = os.path.join('submissions', student[0])
        os.makedirs(subm_dir)
        for filename in contents:
            if filename != 'submit':
                with open(os.path.join(subm_dir, filename), "w+") as f:
                    f.write(contents[filename])
                    f.flush()
                    os.fsync(f.fileno())

        with open(os.path.join(subm_dir, "info.py") , "w+") as f:
            f.write(r"info = {{'emails': {0}, 'submission_id': {1}, 'timestamp': '{2}' }}"
                .format(student, subm_id, timestamp))
            f.flush()
            os.fsync(f.fileno())
        
       
    def get_ids(self, endpoint):
        """Gets the course and assignment id for the given endpoint"""
        response = self.request('assignment')
        for assign in response['data']['results']:
            if assign['name'] == endpoint:
                return assign['id'], assign['course']['id']
        
    def request(self, route, params={}):
        """Makes an API request"""
        return network.api_request(self.access_token, self.args.server, 
            route, client.__version__, log, self.args.insecure, params)
        
    def get_students(self, course):
        """Gets a list of students enrolled in the course"""
        response = self.request('course/{0}/get_students'.format(course),
            {"fields": '{"user":true}'})
        if not response:
            return
        return [student['user']['email'] for student in response['data']]


protocol = ExportProtocol

