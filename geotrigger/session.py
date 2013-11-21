import json
import requests

from version import VERSION, DEBUG

GEOTRIGGER_BASE_URL = 'https://geotrigger.arcgis.com/'
AGO_BASE_URL = 'https://www.arcgis.com/'
AGO_TOKEN_ROUTE = 'sharing/oauth2/token'
AGO_REGISTER_ROUTE = 'sharing/oauth2/registerDevice'

STATUS_OK = 200
STATUS_TOKEN_EXPIRED = 498

class GeotriggerException(Exception):
    pass


def log(msg):
    if DEBUG:
        print(msg)


class GeotriggerSession:
    """
    A base class for Geotrigger Sessions. A Session can be authorized as either
    an Application, which will allow you to manage and administer all aspects
    of your application, or as a Device, which can only access a limited set of
    API functionality.
    """

    def __init__(self, client_id, client_secret=None, access_token=None,
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
        self.expires_in = expires_in
        self.device_id = device_id

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

    def ago_post(self, route, data=None):
        """
        Makes a POST request containing `params` to the specified `route` of
        ArcGIS Online API.
        """
        url = AGO_BASE_URL + route
        log("POST {}".format(url))
        r = requests.post(url, data=data)
        if r.status_code is STATUS_OK:
            return False, r.json()
        else:
            return True, "Request failed. {}: {}".format(r.status_code, r.text)

    def geotrigger_post(self, route, data='{}'):
        """
        Makes a POST request containing `params` to the specified `route` of
        the Geotrigger API
        """

        url = GEOTRIGGER_BASE_URL + route
        headers = {
            'Content-Type': 'application/json',
            'X-GT-Client-Name': 'geotrigger-python',
            'X-GT-Client-Version': VERSION,
        }
        return self.run_request(url, headers=headers, data=data)

    def run_request(self, url, headers={}, data='{}', attempts=0):
        """
        Makes a POST request to the given `url` and returns the raw response.
        """
        if data and isinstance(data, dict):
            data = json.dumps(data)

        headers.update({
            'Authorization': 'Bearer {}'.format(self.access_token),
        })

        log("POST {}".format(url))
        print("\theaders: {}".format(
            ["{}: {}".format(k, v) for k, v in headers.iteritems()]))
        print("\tdata: {}".format(data))

        r = requests.post(url, data=data, headers=headers)

        # Check for HTTP level errors
        if r.status_code is not STATUS_OK:
            raise GeotriggerException(
                "Request failed. {}: {}".format(r.status_code, r.text))

        # Check for application level errors
        resp = r.json()
        if ('error' in resp):
            status_code = resp['error']['code']
            # If token is expired, attempt to refresh it
            if (status_code == STATUS_TOKEN_EXPIRED):
                log("Token expired!")
                self.refresh()
                if attempts < 3:
                    # Retry request with new access_token
                    return self.run_request(url, headers=headers, data=data,
                                            attempts=attempts + 1)
                else:
                    raise GeotriggerException("Could not complete request. "
                                              "Token is expired and cannot be "
                                              "refreshed.")
            else:
                raise GeotriggerException("Error making request. " + r.text)
        else:
            return resp


class GeotriggerApplication(GeotriggerSession):
    def __init__(self, client_id, client_secret, access_token=None,
                 expires_in=None):
        """
        Initializes a new Application Session which will allow you to manage and
        administer all aspects of your application.
        """
        # Sanity check
        if not client_secret:
            raise ValueError('client_secret cannot be empty.')

        GeotriggerSession.__init__(self, client_id=client_id,
                                   client_secret=client_secret,
                                   access_token=access_token,
                                   expires_in=expires_in)

        self.request_token()

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

        err, data = self.ago_post(AGO_TOKEN_ROUTE, params)
        if not err:
            self.access_token = data['access_token']
            self.expires_in = data['expires_in']
        else:
            raise GeotriggerException(
                "Error getting Application token. {}".format(data))

    def refresh(self):
        """
        Refreshes an expired `access_token` for this application.
        """
        log("Refreshing application token.")
        self.request_token()


class GeotriggerDevice(GeotriggerSession):
    def __init__(self, client_id, device_id=None, access_token=None,
                 refresh_token=None, expires_in=None):
        """
        Initializes a new Device Session which only allows access to a limited
        subset of API functionality.
        """
        GeotriggerSession.__init__(self, client_id, device_id=device_id,
                                   access_token=access_token,
                                   refresh_token=refresh_token,
                                   expires_in=expires_in)

        self.register()

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

        err, data = self.ago_post(AGO_REGISTER_ROUTE, params)
        if not err:
            log(data)
            self.device_id = data['device']['deviceId']
            self.access_token = data['deviceToken']['access_token']
            self.refresh_token = data['deviceToken']['refresh_token']
            self.expires_in = data['deviceToken']['expires_in']
        else:
            raise GeotriggerException(
                "Error registering Device. {}".format(data))

    def refresh(self):
        """
        Refreshes an expired `access_token` for this device.
        """
        log("Refreshing device token.")
        params = {
            'client_id': self.client_id,
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token
        }

        err, data = self.ago_post(AGO_TOKEN_ROUTE, params)
        if not err:
            self.access_token = data['access_token']
            self.expires_in = data['expires_in']
        else:
            raise GeotriggerException("Error refreshing token. {}".format(data))
