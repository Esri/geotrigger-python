# -*- coding: utf-8 -*-
import json
from datetime import datetime, timedelta

import requests

from version import VERSION, DEBUG


GEOTRIGGER_BASE_URL = 'https://geotrigger.arcgis.com/'
AGO_BASE_URL = 'https://www.arcgis.com/'
AGO_TOKEN_ROUTE = 'sharing/oauth2/token'
AGO_REGISTER_ROUTE = 'sharing/oauth2/registerDevice'

STATUS_OK = 200
STATUS_TOKEN_EXPIRED = 498

EXPIRES_IN_PADDING = 30


class GeotriggerException(Exception):
    pass


def log(msg):
    if DEBUG:
        print(msg + "\n")


class GeotriggerSession(object):
    """
    A base class for Geotrigger Sessions. A Session can be authorized as either
    an Application, which will allow you to manage and administer all aspects
    of your application, or as a Device, which can only access a limited set of
    API functionality.
    """

    def __init__(self, client_id=None, client_secret=None, access_token=None,
                 refresh_token=None, expires_in=None, device_id=None):
        """
        Initializes a new Geotrigger Session.
        """
        # Sanity check
        if not client_id:
            raise ValueError('client_id cannot be empty.')

        # Save client_id and client_secret
        self.client_id = client_id
        self.client_secret = client_secret

        # Initialize values
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.set_expires(expires_in)
        self.device_id = device_id

    def set_expires(self, expires_in):
        if expires_in is None:
            expires_at = None
        else:
            delta = timedelta(seconds=int(expires_in) - EXPIRES_IN_PADDING)
            expires_at = datetime.now() + delta

        self.expires_in = expires_in
        self.expires_at = expires_at

    def is_device(self):
        """
        Returns true if this session is authenticated as a Device.
        """
        return (self.client_id and not self.client_secret)

    def is_application(self):
        """
        Returns true if this session is authenticated as a Application.
        """
        return (self.client_id and self.client_secret)

    def ago_request(self, route, data=None):
        """
        Makes a GET request to the specified `route` of the ArcGIS Online API,
        sending the given form encoded `data`.
        """
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        url = AGO_BASE_URL + route

        return self.post(url, headers=headers, data=data)

    def geotrigger_request(self, route, data='{}'):
        """
        Makes a authenticated POST request to the specified `route` of the
        Geotrigger API, sending the given `data` as json.
        """
        if isinstance(data, dict):
            data = json.dumps(data)

        # Refresh token if necessary
        if datetime.now() > self.expires_at:
            self.refresh()

        url = GEOTRIGGER_BASE_URL + route
        headers = {
            'Content-Type': 'application/json',
            'X-GT-Client-Name': 'geotrigger-python',
            'X-GT-Client-Version': VERSION,
            'Authorization': 'Bearer ' + self.access_token
        }
        return self.post(url, headers=headers, data=data)

    def post(self, url, data='{}', headers={}):
        """
        Makes a POST request to the given `url` and returns the raw response.
        """
        # Log if in debug mode
        log("POST {}".format(url))
        log("\tHeaders: {}".format(
            ["{}: {}".format(k, v) for k, v in headers.iteritems()]))
        log("\tData: {}".format(data))

        res = requests.post(url, data=data, headers=headers)

        # Check for HTTP errors
        if res.status_code is not STATUS_OK:
            raise GeotriggerException(
                "Request failed. {}: {}".format(res.status_code, res.text))

        # Check for application level errors
        r = res.json()
        log("\tResponse: {}".format(r))
        if ('error' in r):
            if ('code' in r['error']):
                status_code = r['error']['code']
                # If token is expired, attempt to refresh it, then retry the request
                if (status_code == STATUS_TOKEN_EXPIRED):
                    log("Token expired!")
                    self.refresh()
                    if 'Authorization' in headers:
                        headers['Authorization'] = 'Bearer ' + self.access_token
                    return self.post(url, data=data, headers=headers)
            elif ('message' in r['error']):
                raise GeotriggerException(r['error']['message'])
            else:
                raise GeotriggerException("Error making request. " + res.text)
        else:
            return r

    def refresh(self):
        raise NotImplementedError(
            "Implemented in GeotriggerApplication and GeotriggerDevice.")


class GeotriggerApplication(GeotriggerSession):
    """
    An application session requires both a `client_id` and `client_secret` to be
    given. This will allow you to manage and administer all aspects of your
    application.
    """

    def __init__(self, client_id, client_secret, access_token=None,
                 expires_in=None):
        """
        Initializes a new Application Session which will allow you to manage and
        administer all aspects of your application.
        """
        if not client_secret:
            raise ValueError('client_secret cannot be empty.')

        super(self.__class__, self).__init__(
            client_id=client_id,
            client_secret=client_secret,
            access_token=access_token,
            expires_in=expires_in
        )

        if not access_token:
            self.refresh()

    def request_token(self):
        """
        Requests an application token from ArcGIS Online and returns the token
        response.
        """
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials',
            'f': 'json'
        }

        return self.ago_request(AGO_TOKEN_ROUTE, params)

    def refresh(self):
        """
        Refreshes an expired `access_token` for this application.
        """
        if self.access_token:
            log("Refreshing application token.")
        else:
            log("Requesting application token.")

        r = self.request_token()
        self.access_token = r['access_token']
        self.set_expires(r['expires_in'])


class GeotriggerDevice(GeotriggerSession):
    """
    A device session requires only a `client_id` to be given. This will only
    allow access to a limited subset of API functionality, but can be useful for
    impersonating a device.
    """

    def __init__(self, client_id, device_id=None, access_token=None,
                 refresh_token=None, expires_in=None):
        """
        Initializes a new Device Session which only allows access to a limited
        subset of API functionality.
        """
        self.session = super(self.__class__, self).__init__(
            client_id,
            device_id=device_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in
        )

        if not (device_id and access_token and refresh_token):
            device = self.register()
            self.device_id = device['device_id']
            self.access_token = device['access_token']
            self.refresh_token = device['refresh_token']
            self.set_expires(device['expires_in'])

    def register(self):
        """
        Registers a device with ArcGIS Online and returns the device
        registration response.
        """
        params = {
            'client_id': self.client_id,
            'expiration': -1,
            'f': 'json'
        }

        r = self.ago_request(AGO_REGISTER_ROUTE, params)
        return {
            'device_id': r['device']['deviceId'],
            'access_token': r['deviceToken']['access_token'],
            'refresh_token': r['deviceToken']['refresh_token'],
            'expires_in': r['deviceToken']['expires_in']
        }

    def refresh(self):
        """
        Refreshes an expired `access_token` for this device.
        """
        log("Refreshing device token.")
        params = {
            'client_id': self.client_id,
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'f': 'json'
        }

        r = self.ago_request(AGO_TOKEN_ROUTE, params)
        self.access_token = r['access_token']
        self.set_expires(r['expires_in'])
