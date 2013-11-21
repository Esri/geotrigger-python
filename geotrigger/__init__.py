# -*- coding: utf-8 -*-

"""
geotrigger-client-python
~~~~~~~~~~~~~~~~~~~~~~~~

Geotrigger Client is an API client for the ArcGIS Geotrigger Service, a
cloud-hosted geofencing platform, that can send push notifications or notify a
remote server when a mobile device enters or exits an area.

Basic usage:

    >>> from geotrigger import GeotriggerClient
    >>> gt = GeotriggerClient(CLIENT_ID, CLIENT_SECRET)
    >>>
    >>> # list device information for the application
    >>> devices = gt.request("device/list")
    >>> print devices
    >>>
    >>> # list all triggers in the application
    >>> triggers = gt.request("trigger/list")
    >>> print triggers

:copyright: (c) 2013 by Esri.
:license: Apache 2.0, see LICENSE for details.
"""

from geotrigger import GeotriggerClient
from session import GeotriggerDevice, GeotriggerApplication, GeotriggerException

__all__ = [GeotriggerClient, GeotriggerDevice, GeotriggerApplication,
           GeotriggerException]
