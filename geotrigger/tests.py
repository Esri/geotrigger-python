"""
Tests for the Geotrigger module.
"""
import unittest

from mock import patch
from unittest import TestCase
import requests
from geotrigger import GeotriggerClient, GeotriggerDevice, GeotriggerApplication, VERSION
from geotrigger.session import GeotriggerSession, GEOTRIGGER_BASE_URL, AGO_BASE_URL, AGO_REGISTER_ROUTE, AGO_TOKEN_ROUTE


class GeotriggerDeviceTestCase(TestCase):
    def setUp(self):
        self.client_id = 'test_client_id'
        self.device_id = 'test_device_id'
        self.access_token = 'test_access_token'
        self.refresh_token = 'test_refresh_token'
        self.expires_in = 'test_expires_in'
        self.geotrigger_request_headers = {
            'X-GT-Client-Name': 'geotrigger-python',
            'X-GT-Client-Version': VERSION,
            'Content-Type': 'application/json'
        }

        with patch.object(GeotriggerDevice, 'register') as mock_register:
            mock_register.return_value = {
                'device_id': self.device_id,
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
                'expires_in': self.expires_in
            }

            with patch.object(GeotriggerSession, 'request') as mock_request:
                self.client = GeotriggerDevice(self.client_id)

    @patch.object(GeotriggerDevice, 'register')
    @patch.object(GeotriggerSession, 'request')
    def test_register(self, mock_request, mock_register):
        # Device should be registered from setUp
        device = self.client

        # Sanity
        self.assertTrue(device.is_device())
        self.assertFalse(device.is_application())

        # Make sure we set all properties from registration response
        self.assertEqual(device.device_id, self.device_id)
        self.assertEqual(device.access_token, self.access_token)
        self.assertEqual(device.refresh_token, self.refresh_token)
        self.assertEqual(device.expires_in, self.expires_in)

        # Ensure `register` is only called once
        device.register.assert_called_once()

        # Device credentials given, registration should not occur
        device2 = GeotriggerDevice(self.client_id, 'device_id2',
                                   'access_token2', 'refresh_token2',
                                   'expires_in2')

        # `register` should not have been called
        self.assertEqual(device2.register.call_count, 0)



    @patch.object(GeotriggerSession, 'request')
    def test_request(self, mock_request):
        # make a call via the `geotrigger_post` method
        url = 'trigger/list'
        self.client.geotrigger_post(url, data={'tags': 'test_tag'})

        # ensure that the `request` method is called with the correct parameters
        self.client.request.assert_called_once_with(
            GEOTRIGGER_BASE_URL + url,
            headers=self.geotrigger_request_headers,
            data={'tags': 'test_tag'}
        )

class GeotriggerApplicationTestCase(TestCase):
    def setUp(self):
        self.client_id = 'test_client_id'
        self.access_token = 'test_access_token'
        self.client_secret = 'test_client_secret'
        self.expires_in = 'test_expires_in'
        self.geotrigger_request_headers = {
            'X-GT-Client-Name': 'geotrigger-python',
            'X-GT-Client-Version': VERSION,
            'Content-Type': 'application/json'
        }

        with patch.object(GeotriggerApplication, 'request_token') as mock_request_token:
            mock_request_token.return_value = {
                'access_token': self.access_token,
                'expires_in': self.expires_in
            }

            with patch.object(GeotriggerSession, 'request') as mock_request:
                self.client = GeotriggerApplication(self.client_id,
                                               self.client_secret)

    @patch.object(GeotriggerApplication, 'request_token')
    @patch.object(GeotriggerSession, 'request')
    def test_request_token(self, mock_request, mock_request_token):
        # App should be registered from setUp
        app = self.client

        # Sanity
        self.assertTrue(app.is_application())
        self.assertFalse(app.is_device())
        self.assertIsNone(app.device_id)
        self.assertIsNone(app.refresh_token)

        # Make sure we set all properties from token response
        self.assertEqual(app.client_id, self.client_id)
        self.assertEqual(app.access_token, self.access_token)
        self.assertEqual(app.client_secret, self.client_secret)
        self.assertEqual(app.expires_in, self.expires_in)

        # Ensure `request_token` only called once
        app.request_token.assert_called_once()

        # App credentials given, token request should not occur
        app2 = GeotriggerApplication(self.client_id, self.client_secret,
                                     'access_token2', 'expires_in2')

        # `request_token` should not have been called
        self.assertEqual(app2.request_token.call_count, 0)

    @patch.object(GeotriggerSession, 'request')
    def test_request(self, mock_request):
          # make a call via the `geotrigger_post` method
        url = 'trigger/run'
        self.client.geotrigger_post(url, data={'triggerIds': 'test_id'})

        # ensure that the `request` method is called with the correct parameters
        self.client.request.assert_called_once_with(
            GEOTRIGGER_BASE_URL + url,
            headers=self.geotrigger_request_headers,
            data={'triggerIds': 'test_id'}
        )


if __name__ == '__main__':
    unittest.main()