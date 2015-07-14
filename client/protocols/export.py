from client.protocols.common import models
from client.utils import auth
from client.utils import network
from datetime import datetime
from urllib import error
import logging
import os
import pickle

log = logging.getLogger(__name__)

GAE_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
EXPORT_CACHE = "export_cache.pkl"
SUBMISSION_DIR = "submissions"

class ExportProtocol(models.Protocol):
    """Downloads submissions from the server"""

    def run(self, messages):
        """If the --export parameter was used, downloads all submissions
        for the current assignment from the server and then exits
        """
        if not self.args.export:
            return

        self.access_token = auth.authenticate(self.args.authenticate)
        log.info('Authenticated with access token %s', self.access_token)

        data = None
        try:
            data = pickle.load(open(EXPORT_CACHE, "rb"))
        except IOError:
            data = {
                'endpoint': self.assignment.endpoint
            }
            data['assign'], data['course'] = self.get_ids(data['endpoint'])
            data['students'] = self.get_students(data['course'])
            if not data['students']:
                return
            data['current'] = 0

        current_student = 0
        try:
            if not os.path.exists(SUBMISSION_DIR):
                os.makedirs(SUBMISSION_DIR)

            downloads_left = len(data['students']) - data['current']

            print("{0} submissions left to download.".format(downloads_left))

            for current_student in range(data['current'], len(data['students'])):
                student = data['students'][current_student]
                try:
                    self.download_submission(student, data['assign'])
                except (IOError, error.HTTPError):
                    data['current'] = current_student
                    abort(data, len(data['students']), current_student)
                    return
                data['current'] = current_student + 1

        except KeyboardInterrupt:
            pickle.dump(data, open("export_cache.pkl", "wb"))
            abort(data, len(data['students']), current_student)
            return

        print("Submissions downloaded.")
        if os.path.exists(EXPORT_CACHE):
            os.remove(EXPORT_CACHE)

    def download_submission(self, student, assign_id):
        """Downloads a student's final submission for an assignment"""
        if self.args.latest:
            submission = self.get_latest_submission(student, assign_id)
        else:
            submission = self.get_final_submission(student, assign_id)
        if not submission:
            return
        contents, timestamp, subm_id = submission
        subm_dir = os.path.join(SUBMISSION_DIR, student[0])
        if not os.path.exists(subm_dir):
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

    def get_final_submission(self, student, assign_id):
        """Gets the final_submission from the server for use in download_submission"""
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
        return contents, timestamp, subm_id

    def get_latest_submission(self, student, assign_id):
        """Gets the latest submission from the server for use in download_submission"""
        params = {'assignment': assign_id}
        data = self.request('user/{0}/get_submissions'.format(student[0]),
            params)['data']
        if len(data) == 0:
            print("No submissions for {0}".format(student[0]))
            return
        newest_time = None
        newest_subm = None
        for subm in data:
            time = datetime.strptime(subm['server_time'], GAE_DATETIME_FORMAT)
            if newest_time is None or time > newest_time:
                newest_time = time
                newest_subm = subm
        contents = newest_subm['backup']['messages']['file_contents']
        return contents, newest_time, newest_subm['id']

    def get_ids(self, endpoint):
        """Gets the course and assignment id for the given endpoint"""
        response = self.request('assignment')
        for assign in response['data']['results']:
            if assign['name'] == endpoint:
                return assign['id'], assign['course']['id']

    def request(self, route, params={}):
        """Makes an API request"""
        return network.api_request(self.access_token, self.args.server,
            route, self.args.insecure, params)

    def get_students(self, course):
        """Gets a list of students enrolled in the course"""
        response = self.request('course/{0}/get_students'.format(course),
            {"fields": '{"user":true}'})
        if not response:
            return
        return [student['user']['email'] for student in response['data']]

def abort(data, total_students, current_student):
    pickle.dump(data, open(EXPORT_CACHE, "wb"))
    dl_left = total_students - current_student
    print("Download failed. Run the following command to continue:")
    print("    python3 ok --export")
    print("{0} submissions left to download.".format(dl_left))

protocol = ExportProtocol
