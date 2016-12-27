from client.utils import software_update
import client
import json
import mock
import unittest

class CheckVersionTest(unittest.TestCase):
    SERVER = 'test.server'
    PREVIOUS_VERSION = 'v1.1.1'
    CURRENT_VERSION = 'v1.2.3'
    CURRENT_DOWNLOAD_LINK = 'download/link'
    FILE_NAME = 'ok'

    def setUp(self):
        self.patcherGet = mock.patch('requests.get')
        self.addCleanup(self.patcherGet.stop)
        self.mockGet = self.patcherGet.start()

        self.mockContent = self.mockGet.return_value.content
        self.mockJson = self.mockGet.return_value.json

        self.patcherWriteZip = mock.patch('client.utils.software_update._write_zip')
        self.addCleanup(self.patcherWriteZip.stop)
        self.mockWriteZip = self.patcherWriteZip.start()

    def createVersionApiJson(self, current_version, current_download_link):
        self.mockJson.return_value = {
            'data': {
                'results': [
                    {
                        'name': 'ok-client',
                        'current_version': current_version,
                        'download_link': current_download_link,
                    }
                ]
            }
        }

    def testMalformedApiResponse(self):
        self.mockJson.return_value = {'data': []}
        self.assertFalse(software_update.check_version(self.SERVER,
                                                       self.CURRENT_VERSION,
                                                       self.FILE_NAME))

    def testUpToDate(self):
        self.createVersionApiJson(self.CURRENT_VERSION,
                                  self.CURRENT_DOWNLOAD_LINK)

        self.assertTrue(software_update.check_version(self.SERVER,
                                                      self.CURRENT_VERSION,
                                                      self.FILE_NAME))
        self.assertFalse(self.mockWriteZip.called)

    def testNeedsUpdate(self):
        self.createVersionApiJson(self.CURRENT_VERSION,
                                  self.CURRENT_DOWNLOAD_LINK)

        self.assertTrue(software_update.check_version(self.SERVER,
                                                      self.PREVIOUS_VERSION,
                                                      self.FILE_NAME))
        expected_zip_call = ((self.FILE_NAME, self.mockContent),)
        self.assertEqual(expected_zip_call, self.mockWriteZip.call_args)

    def testWriteZip_IOError(self):
        self.createVersionApiJson(self.CURRENT_VERSION,
                                  self.CURRENT_DOWNLOAD_LINK)
        self.mockWriteZip.side_effect = IOError

        self.assertFalse(software_update.check_version(self.SERVER,
                                                       self.PREVIOUS_VERSION,
                                                       self.FILE_NAME))
        self.assertTrue(self.mockWriteZip.called)
