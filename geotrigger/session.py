import json
import requests

from version import VERSION

AGO_BASE_URL = 'https://www.arcgis.com/sharing/'
AGO_TOKEN_URL = AGO_BASE_URL + 'oauth2/token'
AGO_REGISTER_URL = AGO_BASE_URL + 'oauth2/registerDevice'

class GeotriggerException(Exception):
    pass

class Session:
    def __init__(self, client_id, client_secret=None):
        """
        Initializes a new Geotrigger Session.

        If called with a `client_id` and `client_secret`, the session will
        authenticate with the Geotrigger API as an Application, which will
        allow you to manage and administer all aspects of your application.

        If called with only a `client_id`, the session will authenticate with
        the Geotrigger API as a Device, which can only access a limited set of
        API functionality.
        """
        # Sanity check
        if not client_id:
            raise ValueError('client_id cannot be empty.')

        # Save client_id and client_secret
        self.client_id = client_id
        self.client_secret = client_secret

        # Get Application token or register Device
        if self.isApplication():
            application = self.requestToken(client_id, client_secret)
            print(application)
            self.access_token = application['token']
        else:
            device = self.registerDevice(client_id)
            print(device)
            self.access_token = device['token']
            self.refresh_token = device['refresh_token']

    def requestToken(self, client_id, client_secret):
        """
        Requests an application token from ArcGIS Online and returns the token
        response.
        """

        # TODO: request and return token
        return {
            "token": "application_token"
        }

    def registerDevice(self, client_id):
        """
        Registers a device with ArcGIS Online and returns the device
        registration response.
        """

        # TODO: request and return token

        return {
            "token": "device_token",
            "refresh_token": "refresh_token"
        }

    def refresh(self):
        """
        Refreshes an expired `access_token` for this session.
        """
        if self.isApplication():
            # TODO: refresh application credentials
            pass
        else:
            # TODO: refresh device credentials
            pass

    def isDevice(self):
        """
        Returns true if this session is authenticated as a Device.
        """
        return (self.client_id and not self.client_secret)

    def isApplication(self):
        """
        Returns true if this session is authenticated as a Application.
        """
        return (self.client_id and self.client_secret)

    def agoPost(self, route, params):
        """
        Makes a POST request containing `params` to the specified `route` of
        ArcGIS Online API.
        """

        # TODO: make ago post

        return {}

    def geotriggerPost(self, route, params):
        """
        Makes a POST request containing `params` to the specified `route` of
        the Geotrigger API
        """

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(self.access_token),
            'X-GT-Client-Name': 'geotrigger-python',
            'X-GT-Client-Version': VERSION,
        }

        return {}

    def runRequest(self, url, data=None, headers={}, attempts=0):
        """
        Makes a POST request to the given `url` and returns the raw response.
        """:
        if data and isinstance(data, dict):
            data = json.dumps(data)

        print("Making request to: {}".format(url))
        print("\twith data: {}".format(data))
        print("\tand headers: {}".format(
            ["{}: {}".format(k, v) for k,v in headers.iteritems()]))

        r = requests.post(url, data, headers=headers)

        # If token is expired, attempt to refresh it
        if r.status_code == 498:
            self.refresh()
            if attempts < 3:
                self.runRequest(url, data, headers, attempts+1)
            else:
                raise GeotriggerException("Error making request. Token is "
                                          "expired and cannot be refreshed.")
        else:
            return r

