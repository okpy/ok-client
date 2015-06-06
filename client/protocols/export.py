from client.protocols.common import models
from client.utils import auth
from client.utils import network
from datetime import datetime
import client
import logging
import os
import pickle
import sys

log = logging.getLogger(__name__)

GAE_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

class ExportProtocol(models.Protocol):
    """Downloads submissions from the server"""

    def on_interact(self):
        """If the --export parameter was used, downloads all submissions 
        for the given assignment from the server and then exits
        """
        data = None
        try:
            data = pickle.load(open("export_cache.pkl", "rb"))
            self.access_token = auth.authenticate(self.args.authenticate)
            log.info('Authenticated with access token %s', self.access_token)
        except Exception as e:
            if self.args.export:
                data = {}
                self.access_token = auth.authenticate(self.args.authenticate)
                log.info('Authenticated with access token %s', self.access_token)
                data['assign'] = self.args.export
                data['course'] = self.get_course()
                data['students'] = self.get_students(data['course'])
                data['assignid'] = self.get_assign_id(
                    data['course'], data['assign'])
                data['current'] = 0
        
        if data:
            try:
                if not os.path.exists(data['assign']): 
                    os.makedirs(data['assign'])
                
                downloads_left = len(data['students']) - data['current']
                
                print("{0} submissions left to download".format(downloads_left))
                
                for i in range(data['current'], len(data['students'])):
                    student = data['students'][i]
                    try:
                        self.download_submission(student, data['assign'], 
                            data['assignid'])
                        data['current'] = i + 1
                    except Exception as e:
                        data['current'] = i
                        pickle.dump(data, open("export_cache.pkl", "wb"))
                        dl_left = len(data['students']) - i
                        print("Download failed. Run command again to continue.")
                        print("{0} submissions left to download".format(dl_left))
                        sys.exit(0)
                        
            except KeyboardInterrupt:
                pickle.dump(data, open("export_cache.pkl", "wb"))
                dl_left = len(data['students']) - i
                print("Download interrupted. Run command again to continue.")
                print("{0} submissions left to download".format(dl_left))
                sys.exit(0)
                
            print("Submissions downloaded.")
            if os.path.exists('export_cache.pkl'):
                os.remove('export_cache.pkl')
            sys.exit(0)
            
    def get_course(self):
        """Gets a course ID to search for"""
        if self.args.course > 0:
            return self.args.course
        print("Loading course list...")
        response = self.request('course')
        num = 0
        courses = response['data']['results']
        if len(courses) == 1:
            return courses[0]['id']
        elif len(courses) == 0:
            print("No courses found.")
            sys.exit(0)
        for course in courses:
            name = course['display_name']
            offering = course['offering']
            inst = course['institution']
            print("{0}: {1} {2} {3}".format(num, name, offering, inst))
            num += 1
        return courses[int(input("Course #: "))]['id']
        
    def download_submission(self, student, name, assign_id):
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
        subm_dir = name + "/" + student[0]
        os.makedirs(subm_dir)
        for filename in contents:
            if filename != 'submit':
                with open(subm_dir + "/" + filename, "w+") as f:
                    f.write(contents[filename])
                    f.flush()
                    os.fsync(f.fileno())

        with open(subm_dir + "/info.py" , "w+") as f:
            f.write(r"info = {{'emails': {0}, 'submission_id': {1}, 'timestamp': '{2}' }}"
                .format(student, subm_id, timestamp))
            f.flush()
            os.fsync(f.fileno())
        
       
    def get_assign_id(self, course, assign):
        """Gets the id for the given assignment"""
        fields = '{"display_name":true,"id":true}'
        response = self.request('course/{0}/assignments'.format(course),
            {'fields': fields})
        for a in response['data']:
            if a['display_name'] == assign:
                return a['id']
        
    def request(self, route, params={}):
        """Makes an API request"""
        return network.api_request(self.access_token, self.args.server, 
            route, client.__version__, log, self.args.insecure, params)
        
    def get_students(self, course):
        """Gets a list of students enrolled in the course"""
        response = self.request('course/{0}/get_students'.format(course),
            {"fields": '{"user":true}'})
        return [x['user']['email'] for x in response['data']]


protocol = ExportProtocol

