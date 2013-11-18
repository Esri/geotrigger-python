"""
Tests for the Geotrigger module.
"""

from mock import Mock, patch
from unittest import TestCase
from geotrigger import Geotrigger

class GeotriggerTestCase(TestCase):
    @patch.object(Session, 'runRequest')
    def setUp(self, mock_runRequest):
        self.client_id = 1234
        self.client_secret = 5678

        self.test_device =  Geotrigger(self.client_id)
        self.test_application = Geotrigger(self.client_id, self.client_secret)

            