from client.utils import software_update
import client
import json
import mock
import unittest
import urllib.error

class CheckVersionTest(unittest.TestCase):
    SERVER = 'test.server'
    PREVIOUS_VERSION = 'v1.1.1'
    CURRENT_VERSION = 'v1.2.3'
    CURRENT_DOWNLOAD_LINK = 'download/link'
    FILE_NAME = 'ok'

    def setUp(self):
        self.patcherRequest = mock.patch('urllib.request.Request')
        self.addCleanup(self.patcherRequest.stop)
        self.mockRequest = self.patcherRequest.start()

        self.patcherUrlopen = mock.patch('urllib.request.urlopen')
        self.addCleanup(self.patcherUrlopen.stop)
        self.mockUrlopen = self.patcherUrlopen.start()

        self.mockRead = self.mockUrlopen.return_value.read
        self.mockDecode = self.mockUrlopen.return_value.read.return_value.decode

        self.patcherWriteZip = mock.patch('client.utils.software_update._write_zip')
        self.addCleanup(self.patcherWriteZip.stop)
        self.mockWriteZip = self.patcherWriteZip.start()

    def createVersionApiJson(self, current_version, current_download_link):
        self.mockDecode.return_value = json.dumps({
            'data': {
                'results': [
                    {
                        'current_version': current_version,
                        'current_download_link': current_download_link,
                    }
                ]
            }
        })

    def testMalformedApiResponse(self):
        self.mockDecode.return_value = json.dumps({'data': []})
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
        expected_zip_call = ((self.FILE_NAME, self.mockRead.return_value),)
        self.assertEqual(expected_zip_call, self.mockWriteZip.call_args)

    def testWriteZip_IOError(self):
        self.createVersionApiJson(self.CURRENT_VERSION,
                                  self.CURRENT_DOWNLOAD_LINK)
        self.mockWriteZip.side_effect = IOError

        self.assertFalse(software_update.check_version(self.SERVER,
                                                       self.PREVIOUS_VERSION,
                                                       self.FILE_NAME))
        self.assertTrue(self.mockWriteZip.called)

