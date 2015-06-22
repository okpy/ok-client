from client.utils.auth import success_page, success_auth, success_courses, get_file
import unittest


class TemplateGenerationTest(unittest.TestCase):
	
	def write(self, file, html):
		get_file(file, 'w').write(html)
	
	def testCourseGeneration(self):
		response = '[{"year": "2015", "institution": "UC Soumya", "url": "https://ok-server.appspot.com/#/course/5066549580791808", "display_name": "CS 61A", "term": "spring"}]'
		html = success_courses(response,'http://localhost:8080')
		self.assertNotEqual(-1, html.find('2015'))
		self.assertNotEqual(-1, html.find('UC Soumya'))
		self.assertNotEqual(-1, html.find('CS 61A'))
		self.assertNotEqual(-1, html.find('spring'))

	def testCourseGeneration(self):
		response = '[]'
		html, status, byline, title, style, server = success_courses(response, 'http://localhost:8080')
		self.assertEqual(server, 'http://localhost:8080')
		self.assertNotEqual(-1, html.find('It looks like this email is not enrolled'))
		
	def testAuthGeneration(self):
		response = '[{"year": "2015", "institution": "UC Soumya", "url": "https://ok-server.appspot.com/#/course/5066549580791808", "display_name": "CS 61A", "term": "spring"}]'
		html = success_auth(success_courses(response, 'http://localhost:8080'))
		self.assertNotEqual(-1, html.find('Ok!'))
		self.assertNotEqual(-1, html.find('and are currently enrolled'))
		self.assertNotEqual(-1, html.find('1 course'))

	def testAuthGenerationMultiple(self):
		response = '[{"year": "2015", "institution": "UC Soumya", "url": "https://ok-server.appspot.com/#/course/5066549580791808", "display_name": "CS 61A", "term": "spring"}, \
				{"year": "2014", "institution": "UC Soumya", "url": "https://ok-server.appspot.com/#/course/5066549580791808", "display_name": "CS 61B", "term": "spring"}, \
				{"year": "2013", "institution": "UC Soumya", "url": "https://ok-server.appspot.com/#/course/5066549580791808", "display_name": "CS 61C", "term": "spring"}]'
		html = success_auth(success_courses(response, 'http://localhost:8080'))
		self.assertNotEqual(-1, html.find('Ok!'))
		self.assertNotEqual(-1, html.find('and are currently enrolled'))
		self.assertNotEqual(-1, html.find('3 courses'))

	def testAuthEmptyGeneration(self):
		response = '[]'
		html = success_auth(success_courses(response, 'http://localhost:8080'))
		self.assertNotEqual(-1, html.find('Uh oh'))
		self.assertNotEqual(-1, html.find(', but'))
		self.assertNotEqual(-1, html.find('No courses'))
		
	def testAuthColorChange(self):
		response = '[]'
		html = success_auth(success_courses(response, 'http://localhost:8080'))
		self.assertNotEqual(-1, html.find('<style>'))