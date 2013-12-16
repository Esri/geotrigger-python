geotrigger-python
=================

A simple Python client library for interacting with the ArcGIS
Geotrigger Service via the ``GeotriggerClient`` object.

The Geotrigger Service is a cloud-hosted geofencing platform, which
sends push notifications or notifies a remote server when a device
enters or exits an area.

The Geotrigger API manages Application and Device information and
permissions, as well as providing access to create, update, and list
information about Triggers, Tags, and Device Locations.

For more information please refer to the `Geotrigger Service
Documentation <https://developers.arcgis.com/en/geotrigger-service/>`__.

Features
--------

-  Handles authentication and refreshing of credentials
-  Supports making requests as an application, allowing for full
   management of devices, triggers, tags, and permissions
-  Also supports making requests as a device, which can be useful for
   testing purposes

Dependencies
------------

-  Requests (>= 2.1.0)

For running tests, you'll also need:

-  Mock (>= 1.0.1)

Installation
------------

You can install ``geotrigger-python`` from PyPI using the following
command:

.. code:: bash

    pip install geotrigger-python

It's also possible to install from a clone of this repository by running
``setup.py install`` or ``setup.py develop``.

Examples
--------

Using the GeotriggerClient as an application
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This method of using the `GeotriggerClient` is for server-side apps, acting as
the sole owner of your ArcGIS application.

Before continuing, you'll need to find the ``client_id`` and
``client_secret`` for your ArcGIS application on the `ArcGIS for
Developers <https://developers.arcgis.com/en/applications/>`__ site.
You'll find them in the *API Access* section of your applications
details.

**Please make sure to keep your client\_secret secure.** If a third
party obtains your client secret, the will be able to do anything they
want to your Geotrigger application. Your ``client_secret`` should only
be included in server-side applications and should never be distributed
as part of a client-side web or mobile application.

You will need to fill in values for the variable names given in
all-caps.

.. code:: python

    from geotrigger import GeotriggerClient

    # Create a GeotriggerClient as an Application
    gt = GeotriggerClient(CLIENT_ID, CLIENT_SECRET)

    # Fetch a list of all triggers in this application.
    triggers = gt.request('trigger/list')

    # Print all the triggers and any tags applied to them.
    print "\nFound %d triggers:" % len(triggers['triggers'])
    for t in triggers['triggers']:
        print "- %s (%s)" % (t['triggerId'], ",".join(t['tags']))

    # Add "testing123" tag to all of the triggers that we fetched above.
    triggers_updated = gt.request('trigger/update', {
        'triggerIds': [t['triggerId'] for t in triggers['triggers']],
        'addTags': TAG
    })

    # Print the updated triggers.
    print "\nUpdated %d triggers:" % len(triggers_updated['triggers'])
    for t in triggers_updated['triggers']:
        print "- %s (%s)" % (t['triggerId'], ",".join(t['tags']))

    # Delete the "testing123" tag from the application.
    tags_deleted = gt.request('tag/delete', {'tags': TAG})
    print '\nDeleted tags: "%s"' % ", ".join(tags_deleted.keys())

Using the GeotriggerClient as a Device
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``GeotriggerClient`` can also be used as if it were a device, which
will allow you to send location updates and fire triggers, but you will
not be able to receive any Geotrigger notifications, because they are sent as
push messages to actual mobile devices. You can use the
`trigger/history <https://developers.arcgis.com/en/geotrigger-service/api-reference/trigger-history/>`__
API route or configure your triggers with a ``callbackUrl`` in order to
observe that triggers are being fired.

You'll only need the ``client_id`` for your application in order to use
the ``GeotriggerClient`` as a device.

For testing callback triggers, you can use the handy
`RequestBin <http://requestb.in>`__ service. Create a new bin and
provide its URL as the ``callbackUrl`` when creating a trigger.

You will need to fill in values for the variable names given in
all-caps.

.. code:: python

    from geotrigger import GeotriggerClient

    # Create a GeotriggerClient as a device
    gt = GeotriggerClient(CLIENT_ID)

    # Default tags are created for all devices and triggers. Device default tags
    # can be used when you want to allow devices to create triggers that only they
    # can fire. Default tags look like: 'device:device_id' or 'trigger:trigger_id'
    device_tag = 'device:%s' % gt.session.device_id

    # Build a callback trigger, using your default tag and RequestBin URL.
    esri_hq = {
        'condition': {
            'geo': {
                'latitude': 34.0562,
                'longitude': -117.1956,
                'distance': 100
            },
            'direction': 'enter'
        },
        'action': {
            'callbackUrl': CALLBACK_URL
        },
        'setTags': device_tag
    }

    # Post the trigger to the Geotrigger API
    trigger = gt.request('trigger/create', esri_hq)
    print trigger

    # Construct a fake location update to send to the Geotrigger API.
    # Supplying a previous location is not strictly required, but will speed up
    # trigger processing by avoiding a database lookup.
    location_update = {
        'previous': {
            'timestamp': datetime.now().isoformat(),
            'latitude': 45.5165,
            'longitude': -122.6764,
            'accuracy': 5,
        },
        'locations': [
            {
                'timestamp': datetime.now().isoformat(),
                'latitude': 34.0562,
                'longitude': -117.1956,
                'accuracy': 5,
            }
        ]
    }

    # Send the location update.
    update_response = gt.request('location/update', location_update)
    print update_response

Shortly after running the above code, you will see a POST to your
callback url.

Advanced GeotriggerClient usage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you already have an ArcGIS Application ``access_token`` that you'd
like to use to create a ``GeotriggerClient``, pass in a
``GeotriggerApplication`` as the ``session`` kwarg. You may want to do this if
you are integrating Geotrigger functionality into an application that
already obtains credentials from ArcGIS Online.

Similarly, if you want to impersonate an existing device for which you
already have a ``client_id``, ``device_id``, ``access_token``, and
``refresh_token``, you can create your own ``GeotriggerDevice`` to pass
into the ``GeotriggerClient``. This can be used to debug apps that are
being developed with the Geotrigger SDKs for Android and iOS.

.. code:: python

    from geotrigger import GeotriggerClient, GeotriggerApplication, GeotriggerDevice

    app = GeotriggerApplication(CLIENT_ID, CLIENT_SECRET, ACCESS_TOKEN)
    app_client = GeotriggerClient(session=app)

    device = GeotriggerDevice(CLIENT_ID, DEVICE_ID, ACCESS_TOKEN, REFRESH_TOKEN)
    device_client = GeotriggerClient(session=device)

Issues
~~~~~~

Find a bug or want to request a new feature? Please let us know by submitting an issue.

Contributing
~~~~~~~~~~~~

Esri welcomes contributions from anyone and everyone. Please see our `guidelines for contributing <https://github.com/esri/contributing>`__.

Licensing
~~~~~~~~~

Copyright 2013 Esri

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

A copy of the license is available in the LICENSE file.
