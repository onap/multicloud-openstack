# Copyright (c) 2017-2018 Wind River Systems, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import mock

import unittest
import json
import urllib2

from titanium_cloud.vesagent import vespublish

MOCK_VESENDPOINT = {
    "endpoint" : "MOCKED_VES_COLLECTOR_EP1",
    "username" : "MOCKED_VES_COLLECTOR_USER1",
    "password" : "MOCKED_VES_COLLECTOR_PASSWD1",
}
MOCK_VESPUBLISH_EVENT1 = [{"name":"event1"}]

class VespublishTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @mock.patch.object(urllib2, 'urlopen')
    @mock.patch.object(urllib2, 'Request')
    def test_publishAnyEventToVES(self, mock_Request, mock_urlopen):
        mock_request = mock.Mock()

        mock_Request.side_effect= [
            mock_request
                ]

        mock_response = mock.Mock(["read"])
        mock_response.read.return_value = "MOCKED_VESPUBLISH_RESPONSE_MESSAGE"
        mock_urlopen.side_effect= [
            mock_response
                ]

        vespublish.publishAnyEventToVES(MOCK_VESENDPOINT, MOCK_VESPUBLISH_EVENT1)

        pass
