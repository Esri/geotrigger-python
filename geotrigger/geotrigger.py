import json
import os
import sys
import urllib

from version import VERSION
from urllib2 import HTTPError, URLError

from session import Session

API_VERSION = 1
GEOTRIGGERS__BASE_URL = 'https://geotrigger.arcgis.com/'


class Geotrigger:
    """
    A simple wrapper for the Geotrigger API.
    """
    def __init__(self, client_id=None, client_secret=None):
        """
        Initializes a new instance of the Geotrigger API client.

        This client supports authenticating with the Geotrigger API as either
        an Application or a Device. Applications must provide a `client_id` and
        `client_secret`.

        """
        self.session = Session(client_id, client_secret)

