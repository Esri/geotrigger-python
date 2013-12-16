from os import sys, path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

import requests

from datetime import datetime
from geotrigger import GeotriggerClient

CLIENT_ID = 'YOUR_CLIENT_ID'


def device_example():
    # Create the GeotriggerClient using only a client_id, a device will be
    # registered for you.
    print 'Creating GeotriggerClient as a device.'
    gt = GeotriggerClient(CLIENT_ID)

    # Get the default tag for our fake device so that we can apply it to
    # the trigger that we'll be creating.
    device_tag = 'device:%s' % gt.session.device_id

    # Create a unique URL for this example on RequestBin, a super handy HTTP
    # request inspection tool. (See: http://requestb.in)
    r = requests.post('http://requestb.in/api/v1/bins', {'private': True})
    if r.status_code == 200:
        bin = r.json()
        requestbin_url = 'http://requestb.in/%s' % bin['name']
    else:
        print "Could not set up a requestb.in URL to use for trigger callback."
        print "(%d) %s" % (r.status_code, r.text)
        sys.exit(1)

    # Build trigger
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
            'callbackUrl': requestbin_url
        },
        'setTags': device_tag
    }

    # Post the trigger to the Geotrigger API
    print 'Creating trigger...'
    trigger_response = gt.request('trigger/create', esri_hq)
    print trigger_response

    # Construct a fake location update to send to the Geotrigger API.
    # Supplying a previous location is not strictly required, but will speed up
    # trigger processing if provided.
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
    print 'Sending location update...'
    update_response = gt.request('location/update', location_update)
    print update_response

    # Visit the requestb.in url to inspect the request made to the callback url.
    print 'Check %s?inspect for the trigger callback!' % requestbin_url


if __name__ == '__main__':
    device_example()