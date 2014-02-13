# -*- coding: utf-8 -*-

import unittest
from unittest import TestCase
from datetime import datetime, timedelta
import json

from mock import patch

from geotrigger import GeotriggerClient, GeotriggerDevice, \
    GeotriggerApplication, __version__
from geotrigger.session import GeotriggerSession, GEOTRIGGER_BASE_URL, \
    AGO_TOKEN_ROUTE, EXPIRES_IN_PADDING


class GeotriggerClientTestCase(TestCase):
    """
    Tests for the `GeotriggerClient` class.
    """

    def setUp(self):
        self.client_id = 'test_client_id'
        self.client_secret = 'test_client_secret'
        self.device_id = 'test_device_id'
        self.access_token = 'test_access_token'
        self.refresh_token = 'test_refresh_token'
        self.expires_in = 100

    @patch.object(GeotriggerDevice, 'register')
    def test_device_init(self, mock_register):
        """
        Test initialization of the `GeotriggerClient` as a device.
        """
        mock_register.return_value = {
            'device_id': self.device_id,
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'expires_in': self.expires_in
        }
        gt = GeotriggerClient(client_id=self.client_id)

        self.assertIsNotNone(gt.session)
        self.assertTrue(gt.session.is_device())
        self.assertEqual(gt.session.client_id, self.client_id)
        gt.session.register.assert_called_once()


    @patch.object(GeotriggerDevice, 'register')
    def test_device_init_manual(self, mock_register):
        gt = GeotriggerClient(session=GeotriggerDevice(self.client_id,
                                                       self.device_id,
                                                       self.access_token,
                                                       self.refresh_token))
        self.assertIsNotNone(gt.session)
        self.assertTrue(gt.session.is_device())
        self.assertEqual(gt.session.client_id, self.client_id)
        self.assertEqual(gt.session.register.call_count, 0)

    @patch.object(GeotriggerApplication, 'request_token')
    def test_application_init(self, mock_request_token):
        """
        Test initialization of the 'GeotriggerClient` as an application.
        """
        mock_request_token.return_value = {
            'access_token': self.access_token,
            'expires_in': self.expires_in
        }
        gt = GeotriggerClient(client_id=self.client_id,
                              client_secret=self.client_secret)

        self.assertIsNotNone(gt.session)
        self.assertTrue(gt.session.is_application())
        self.assertEqual(gt.session.client_id, self.client_id)
        gt.session.request_token.assert_called_once()

    @patch.object(GeotriggerApplication, 'request_token')
    def test_application_init_manual(self, mock_request_token):
        gt = GeotriggerClient(session=GeotriggerApplication(self.client_id,
                                                            self.client_secret,
                                                            self.access_token))
        self.assertIsNotNone(gt.session)
        self.assertTrue(gt.session.is_application())
        self.assertEqual(gt.session.client_id, self.client_id)
        self.assertEqual(gt.session.request_token.call_count, 0)


class GeotriggerDeviceTestCase(TestCase):
    """
    Tests for the `GeotriggerDevice` class.
    """

    def setUp(self):
        self.client_id = 'device_client_id'
        self.device_id = 'device_device_id'
        self.access_token = 'device_access_token'
        self.refresh_token = 'device_refresh_token'
        self.expires_in = 200
        self.tag = 'device_tag'

        self.geotrigger_headers = {
            'X-GT-Client-Name': 'geotrigger-python',
            'X-GT-Client-Version': __version__,
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + self.access_token
        }

        with patch.object(GeotriggerDevice, 'register') as mock_register:
            mock_register.return_value = {
                'device_id': self.device_id,
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
                'expires_in': self.expires_in
            }

            with patch.object(GeotriggerSession, 'post') as mock_post:
                self.client = GeotriggerDevice(self.client_id)

    @patch.object(GeotriggerDevice, 'register')
    @patch.object(GeotriggerSession, 'post')
    def test_register(self, mock_post, mock_register):
        """
        Test device registration with ArcGIS Online.
        """
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
        self.assertIsNotNone(device.expires_at)

        # Ensure `register` is only called once
        device.register.assert_called_once()

        # Device credentials given, registration should not occur
        device2 = GeotriggerDevice(self.client_id, 'device_id',
                                   'access_token', 'refresh_token',
                                   300)

        # `register` should not have been called
        self.assertEqual(device2.register.call_count, 0)

    @patch.object(GeotriggerSession, 'post')
    def test_geotrigger_request(self, mock_post):
        """
        Test creation of Geotrigger API requests.
        """
        # make a call via the `geotrigger_post` method
        data = {'tags': self.tag}
        url = 'trigger/list'
        self.client.geotrigger_request(url, data=data)

        # ensure that the `request` method is called with the correct parameters
        self.client.post.assert_called_once_with(
            GEOTRIGGER_BASE_URL + url,
            data=json.dumps(data),
            headers=self.geotrigger_headers
        )

    @patch.object(GeotriggerSession, 'post')
    @patch.object(GeotriggerSession, 'ago_request')
    def test_refresh(self, mock_ago_request, mock_post):
        """
        Test refresh of expired access tokens.
        """
        first_token = 'new_token'
        first_expires = 400
        second_token = 'newer_token'
        second_expires = 401

        mock_ago_request.return_value = {
            'access_token': first_token,
            'expires_in': first_expires
        }

        old_token = self.client.access_token
        old_expires = self.client.expires_in

        # sanity
        self.assertEqual(self.access_token, old_token)
        self.assertEqual(self.expires_in, old_expires)

        # call refresh
        self.client.refresh()

        # check refresh request
        self.client.ago_request.assert_called_once_with(
            AGO_TOKEN_ROUTE,
            {
                'client_id': self.client_id,
                'refresh_token': self.refresh_token,
                'grant_type': 'refresh_token',
                'f': 'json'
            }
        )

        # check token
        self.assertEqual(self.client.access_token, first_token)
        self.assertEqual(self.client.expires_in, first_expires)

        # make a geotrigger request to ensure that we call refresh again
        with patch.object(GeotriggerDevice, 'refresh') as mock_refresh:
            mock_refresh.return_value = {
                'access_token': second_token,
                'expires_in': second_expires
            }

            # force expire credentials
            self.client.set_expires(0)

            # sanity
            self.assertEqual(self.client.refresh.call_count, 0)

            # make a geotrigger request, which should call refresh
            self.client.geotrigger_request('dummy/url')

            # check refresh call count
            self.assertEqual(self.client.refresh.call_count, 1)


class GeotriggerApplicationTestCase(TestCase):
    """
    Tests for the GeotriggerApplication class.
    """

    def setUp(self):
        self.client_id = 'app_client_id'
        self.access_token = 'app_access_token'
        self.client_secret = 'app_client_secret'
        self.expires_in = 500
        self.geotrigger_headers = {
            'X-GT-Client-Name': 'geotrigger-python',
            'X-GT-Client-Version': __version__,
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + self.access_token
        }

        with patch.object(GeotriggerApplication,
                          'request_token') as mock_request_token:
            mock_request_token.return_value = {
                'access_token': self.access_token,
                'expires_in': self.expires_in
            }

            with patch.object(GeotriggerSession, 'post') as mock_request:
                self.client = GeotriggerApplication(self.client_id,
                                                    self.client_secret)

    @patch.object(GeotriggerApplication, 'request_token')
    @patch.object(GeotriggerSession, 'post')
    def test_request_token(self, mock_post, mock_request_token):
        """
        Test application token requests to ArcGIS Online.
        """
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
        self.assertIsNotNone(app.expires_at)

        # Ensure `request_token` only called once
        app.request_token.assert_called_once()

        # App credentials given, token request should not occur
        app2 = GeotriggerApplication(self.client_id, self.client_secret,
                                     'access_token', 600)

        # `request_token` should not have been called
        self.assertEqual(app2.request_token.call_count, 0)

    @patch.object(GeotriggerSession, 'post')
    def test_geotrigger_request(self, mock_request):
        """
        Test creation of Geotrigger API requests.
        """
        # make a call via the `geotrigger_post` method
        data = {'triggerIds': 'trigger_id'}
        url = 'trigger/run'
        self.client.geotrigger_request(url, data=data)

        # ensure that the `post` method is called with the correct parameters
        self.client.post.assert_called_once_with(
            GEOTRIGGER_BASE_URL + url,
            headers=self.geotrigger_headers,
            data=json.dumps(data)
        )

    @patch.object(GeotriggerSession, 'post')
    @patch.object(GeotriggerSession, 'ago_request')
    def test_refresh(self, mock_ago_request, mock_post):
        """
        Test refresh of expired access tokens.
        """
        first_token = 'new_token'
        first_expires = 700
        second_token = 'newer_token'
        second_expires = 701
        mock_ago_request.return_value = {
            'access_token': first_token,
            'expires_in': first_expires
        }

        old_token = self.client.access_token
        old_expires = self.client.expires_in

        # sanity
        self.assertEqual(self.access_token, old_token)
        self.assertEqual(self.expires_in, old_expires)

        # call refresh
        self.client.refresh()

        # check refresh request
        self.client.ago_request.assert_called_once_with(
            AGO_TOKEN_ROUTE,
            {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'client_credentials',
                'f': 'json'
            }
        )

        # check refreshed token
        self.assertEqual(self.client.access_token, first_token)
        self.assertEqual(self.client.expires_in, first_expires)

        # make a geotrigger request to ensure that we call refresh again
        with patch.object(GeotriggerApplication, 'refresh') as mock_refresh:
            mock_refresh.return_value = {
                'access_token': second_token,
                'expires_in': second_expires
            }

            # force expire credentials
            self.client.set_expires(0)

            # sanity
            self.assertEqual(self.client.refresh.call_count, 0)

            # make a geotrigger request, which should call refresh
            self.client.geotrigger_request('dummy/url')

            # check refresh call count
            self.assertEqual(self.client.refresh.call_count, 1)


class GeotriggerSessionTestCase(TestCase):
    """
    Tests for the `GeotriggerSession` class.
    """

    def setUp(self):
        self.client_id = 'test_client_id'
        self.client_secret = 'test_client_secret'
        self.device_id = 'test_device_id'
        self.access_token = 'test_access_token'
        self.refresh_token = 'test_refresh_token'
        self.expires_in = 800
        self.expires_delta = timedelta(seconds=self.expires_in-EXPIRES_IN_PADDING)
        self.fudge_factor = timedelta(seconds=0.1)

    def test_set_expires(self):
        """
        Test that expires_at is correctly set from the value of expires_in.
        """
        expected = datetime.now() + self.expires_delta
        session = GeotriggerSession(self.client_id, self.client_secret,
                                         self.access_token, self.refresh_token,
                                         self.expires_in, self.device_id)

        self.assertIsNotNone(session.expires_in)
        self.assertIsNotNone(session.expires_at)
        self.assertAlmostEqual(expected, session.expires_at, delta=self.fudge_factor)

if __name__ == '__main__':
    unittest.main()