# -*- coding: utf-8 -*-

from session import GeotriggerApplication, GeotriggerDevice


class GeotriggerClient:
    """
    A simple interface to the Geotrigger API.
    """

    def __init__(self, client_id=None, client_secret=None, session=None):
        """
        Initializes a new instance of the Geotrigger API client.

        This client supports authenticating with the Geotrigger API as either
        an Application or a Device.

        If instantiated with both a `client_id` and `client_secret`, the
        GeotriggerClient will authenticate as an Application. This will allow
        you full access to the API, permitting administration of triggers, tags,
        and devices for your application.

        If instantiated with only a `client_id`, the `GeotriggerClient` will
        automatically register a Geotrigger Device with ArcGIS Online, which
        will only have permission to access a subset of the Geotrigger API.
        This mode of operation is useful for simulating location updates sent
        from devices.

        You can also create a session manually if you need more control over the
        GeotriggerClient. This can be used to impersonate an existing device
        within your application, or could be useful if you already have
        credentials that can be used with the Geotrigger API.
        """

        if client_id and client_secret:
            self.session = GeotriggerApplication(client_id, client_secret)
        elif client_id:
            self.session = GeotriggerDevice(client_id)
        elif session:
            self.session = session
        else:
            raise ValueError("You must specify a client_id or session.")


    def request(self, route, data='{}'):
        """
        Makes a Geotrigger API request to the given `route`.
        The optional `data` parameter can be either a dict or a json string.
        """
        return self.session.geotrigger_request(route, data=data)