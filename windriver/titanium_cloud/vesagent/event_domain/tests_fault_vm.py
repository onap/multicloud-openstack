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

from titanium_cloud.vesagent.vespublish import publishAnyEventToVES
from common.utils import restcall
from titanium_cloud.vesagent.event_domain import fault_vm

MOCK_TOKEN_RESPONSE = {"access":{"token":{"issued_at":"2018-05-10T16:56:56.000000Z","expires":"2018-05-10T17:56:56.000000Z","id":"4a832860dd744306b3f66452933f939e","tenant":{"domain":{"id":"default","name":"Default"},"enabled":"true","id":"0e148b76ee8c42f78d37013bf6b7b1ae","name":"VIM"}},"serviceCatalog":[],"user":{"domain":{"id":"default","name":"Default"},"id":"ba76c94eb5e94bb7bec6980e5507aae2","name":"demo"}}}
MOCK_SERVERS_GET_RESPONSE = {"servers": [{"id": "c4b575fa-ed85-4642-ab4b-335cb5744721", "links": [{"href": "http://10.12.25.2:8774/v2.1/0e148b76ee8c42f78d37013bf6b7b1ae/servers/c4b575fa-ed85-4642-ab4b-335cb5744721", "rel": "self"}, {"href": "http://10.12.25.2:8774/0e148b76ee8c42f78d37013bf6b7b1ae/servers/c4b575fa-ed85-4642-ab4b-335cb5744721", "rel": "bookmark"}], "name": "onap-aaf"}]}
MOCK_BACKLOG_INPUT = {"backlog_uuid": "ce2d7597-22e1-4239-890f-bc303bd67076",
                                              "server_id": "c4b575fa-ed85-4642-ab4b-335cb5744721",
                                              "tenant_id": "0e148b76ee8c42f78d37013bf6b7b1ae", "api_method": "GET",
                                              "source": "onap-aaf",
                                              "api_link": "/onaplab_RegionOne/compute/v2.1/0e148b76ee8c42f78d37013bf6b7b1ae/servers/c4b575fa-ed85-4642-ab4b-335cb5744721",
                                              "domain": "fault", "type": "vm", "tenant": "VIM"}
class FaultVMTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_epoch_now_usecond(self):
        epoch = fault_vm.get_epoch_now_usecond()
        self.assertGreater(epoch, 1)
        pass


    @mock.patch.object(restcall, '_call_req')
    def test_buildBacklog_fault_vm(self, mock_call_req):

        mock_call_req.side_effect= [
            (0, json.dumps(MOCK_TOKEN_RESPONSE), "MOCKED response body"),
            (0, json.dumps(MOCK_SERVERS_GET_RESPONSE), "MOCKED response body")
                ]
        backlog = fault_vm.buildBacklog_fault_vm(vimid="windriver-hudson-dc_RegionOne",
                                                        backlog_input = MOCK_BACKLOG_INPUT)
        self.assertIsNotNone(backlog)
        pass
