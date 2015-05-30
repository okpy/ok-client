from client.utils.auth import success_page, success_auth, success_courses, get_file
import unittest

class SuccessPageTest(unittest.TestCase):
	
	def write(self, file, html):
		get_file('../../tests/templates/'+file, 'w').write(html)
	
	def testCourseGeneration(self):
		response = '[{"year": "2015", "institution": "UC Soumya", "url": "https://ok-server.appspot.com/#/course/5066549580791808", "display_name": "CS 61A", "term": "spring"}]'
		html = success_courses(response)
		self.write('test.partial.course.html', html)
		assert html.find('2015') != -1
		assert html.find('UC Soumya') != -1
		assert html.find('CS 61A') != -1
		assert html.find('spring') != -1

	def testCourseGeneration(self):
		response = '[]'
		html, status, byline, title = success_courses(response)
		self.write('test.partial.nocourses.html', html)
		assert html.find('It looks like this email is not enrolled') != -1
		
	def testAuthGeneration(self):
		response = '[{"year": "2015", "institution": "UC Soumya", "url": "https://ok-server.appspot.com/#/course/5066549580791808", "display_name": "CS 61A", "term": "spring"}]'
		html = success_auth(success_courses(response), 'http://localhost:8080')
		self.write('test.auth.html', html)

	def testAuthEmptyGeneration(self):
		response = '[]'
		html = success_auth(success_courses(response), 'http://localhost:8080')
		self.write('test.auth.empty.html', html)