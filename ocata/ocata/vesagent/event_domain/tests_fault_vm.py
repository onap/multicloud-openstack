# Copyright (c) Intel Corporation, Inc.
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

from ocata.vesagent import vespublish
from common.utils import restcall
from ocata.vesagent.event_domain import fault_vm

MOCK_TOKEN_RESPONSE = {"access":{"token":{"issued_at":"2018-05-10T16:56:56.000000Z","expires":"2018-05-10T17:56:56.000000Z","id":"4a832860dd744306b3f66452933f939e","tenant":{"domain":{"id":"default","name":"Default"},"enabled":"true","id":"0e148b76ee8c42f78d37013bf6b7b1ae","name":"VIM"}},"serviceCatalog":[],"user":{"domain":{"id":"default","name":"Default"},"id":"ba76c94eb5e94bb7bec6980e5507aae2","name":"demo"}}}
MOCK_SERVERS_GET_RESPONSE = {"servers": [{"id": "c4b575fa-ed85-4642-ab4b-335cb5744721", "links": [{"href": "http://10.12.25.2:8774/v2.1/0e148b76ee8c42f78d37013bf6b7b1ae/servers/c4b575fa-ed85-4642-ab4b-335cb5744721", "rel": "self"}, {"href": "http://10.12.25.2:8774/0e148b76ee8c42f78d37013bf6b7b1ae/servers/c4b575fa-ed85-4642-ab4b-335cb5744721", "rel": "bookmark"}], "name": "onap-aaf"}]}
MOCK_BACKLOG_INPUT = {"backlog_uuid": "ce2d7597-22e1-4239-890f-bc303bd67076",
                                              "server_id": "c4b575fa-ed85-4642-ab4b-335cb5744721",
                                              "tenant_id": "0e148b76ee8c42f78d37013bf6b7b1ae", "api_method": "GET",
                                              "source": "onap-aaf",
                                              "api_link": "/onaplab_RegionOne/compute/v2.1/0e148b76ee8c42f78d37013bf6b7b1ae/servers/c4b575fa-ed85-4642-ab4b-335cb5744721",
                                              "domain": "fault", "type": "vm", "tenant": "VIM"}

MOCK_BACKLOG_INPUT_wo_tenant_id = {"backlog_uuid": "ce2d7597-22e1-4239-890f-bc303bd67076",
                                              "server_id": "c4b575fa-ed85-4642-ab4b-335cb5744721",
                                              "source": "onap-aaf",
                                              "api_link": "/onaplab_RegionOne/compute/v2.1/0e148b76ee8c42f78d37013bf6b7b1ae/servers/c4b575fa-ed85-4642-ab4b-335cb5744721",
                                              "domain": "fault", "type": "vm", "tenant": "VIM"}
MOCK_BACKLOG_INPUT_wo_tenant = {"backlog_uuid": "ce2d7597-22e1-4239-890f-bc303bd67076",
                                              "server_id": "c4b575fa-ed85-4642-ab4b-335cb5744721",
                                              "source": "onap-aaf",
                                              "domain": "fault", "type": "vm", }

MOCK_BACKLOG_INPUT_wo_server_id = {"source": "onap-aaf",
                                              "domain": "fault", "type": "vm", "tenant": "VIM"}
MOCK_BACKLOG_INPUT_wo_server = {"domain": "fault", "type": "vm", "tenant": "VIM"}

MOCK_SERVER_GET_RESPONSE = {"server": {"wrs-res:topology": "node:0,  4096MB, pgsize:2M, vcpus:0,1, pol:sha", "OS-EXT-STS:task_state": None, "addresses": {"oam_onap_BTHY": [{"OS-EXT-IPS-MAC:mac_addr": "fa:16:3e:6c:0d:6b", "version": 4, "addr": "10.0.13.1", "OS-EXT-IPS:type": "fixed"}, {"OS-EXT-IPS-MAC:mac_addr": "fa:16:3e:6c:0d:6b", "version": 4, "addr": "10.12.5.185", "OS-EXT-IPS:type": "floating"}]}, "links": [], "image": {"id": "6e219e86-cd94-4989-9119-def29aa10b12", "links": []}, "wrs-if:nics": [], "wrs-sg:server_group": "", "OS-EXT-STS:vm_state": "active", "OS-SRV-USG:launched_at": "2018-04-26T08:01:28.000000", "flavor": {}, "id": "c4b575fa-ed85-4642-ab4b-335cb5744721", "security_groups": [{"name": "onap_sg_BTHY"}], "user_id": "ba76c94eb5e94bb7bec6980e5507aae2", "OS-DCF:diskConfig": "MANUAL", "accessIPv4": "", "accessIPv6": "", "progress": 0, "OS-EXT-STS:power_state": 1, "OS-EXT-AZ:availability_zone": "nova", "metadata": {}, "status": "ACTIVE", "updated": "2018-04-26T08:01:28Z", "hostId": "17acc9f2ae4f618c314e4cdf0c206585b895bc72a9ec57e57b254133", "OS-SRV-USG:terminated_at": None, "wrs-res:pci_devices": "", "wrs-res:vcpus": [2, 2, 2], "key_name": "onap_key_BTHY", "name": "onap-aaf", "created": "2018-04-26T08:01:20Z", "tenant_id": "0e148b76ee8c42f78d37013bf6b7b1ae", "os-extended-volumes:volumes_attached": [], "config_drive": ""}}

MOCK_SERVER_GET_RESPONSE_empty = {}

MOCK_vesAgentConfig = {"backlogs": [{"backlog_uuid": "ce2d7597-22e1-4239-890f-bc303bd67076",
                                              "server_id": "c4b575fa-ed85-4642-ab4b-335cb5744721",
                                              "tenant_id": "0e148b76ee8c42f78d37013bf6b7b1ae", "api_method": "GET",
                                              "source": "onap-aaf",
                                              "api_link": "/onaplab_RegionOne/compute/v2.1/0e148b76ee8c42f78d37013bf6b7b1ae/servers/c4b575fa-ed85-4642-ab4b-335cb5744721",
                                              "domain": "fault", "type": "vm", "tenant": "VIM"}],
                                "poll_interval_default": 10, "vimid": "windriver-hudson-dc_RegionOne",
                                "ves_subscription": {"username": "user", "password": "password",
                                                 "endpoint": "http://127.0.0.1:9005/sample"}}

MOCK_vesAgentState = {"ce2d7597-22e1-4239-890f-bc303bd67076": {"timestamp": 1525975400}}
MOCK_oneBacklog = {"backlog_uuid": "ce2d7597-22e1-4239-890f-bc303bd67076", "server_id": "c4b575fa-ed85-4642-ab4b-335cb5744721", "tenant_id": "0e148b76ee8c42f78d37013bf6b7b1ae", "api_method": "GET", "source": "onap-aaf", "api_link": "/onaplab_RegionOne/compute/v2.1/0e148b76ee8c42f78d37013bf6b7b1ae/servers/c4b575fa-ed85-4642-ab4b-335cb5744721", "domain": "fault", "type": "vm", "tenant": "VIM"}

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

    @mock.patch.object(restcall, '_call_req')
    def test_buildBacklog_fault_vm_wo_tenant_id(self, mock_call_req):

        mock_call_req.side_effect= [
            (0, json.dumps(MOCK_TOKEN_RESPONSE), "MOCKED response body"),
            (0, json.dumps(MOCK_SERVERS_GET_RESPONSE), "MOCKED response body")
                ]
        backlog = fault_vm.buildBacklog_fault_vm(vimid="windriver-hudson-dc_RegionOne",
                                                        backlog_input = MOCK_BACKLOG_INPUT_wo_tenant_id)
        self.assertIsNotNone(backlog)
        pass

    @mock.patch.object(restcall, '_call_req')
    def test_buildBacklog_fault_vm_wo_tenant(self, mock_call_req):

        mock_call_req.side_effect= [
            (1, json.dumps(MOCK_TOKEN_RESPONSE), "MOCKED response body: failed"),
            (0, json.dumps(MOCK_SERVERS_GET_RESPONSE), "MOCKED response body")
                ]
        backlog = fault_vm.buildBacklog_fault_vm(vimid="windriver-hudson-dc_RegionOne",
                                                        backlog_input = MOCK_BACKLOG_INPUT_wo_tenant)
        self.assertIsNone(backlog)
        pass

    @mock.patch.object(restcall, '_call_req')
    def test_buildBacklog_fault_vm_wo_server_id(self, mock_call_req):

        mock_call_req.side_effect= [
            (0, json.dumps(MOCK_TOKEN_RESPONSE), "MOCKED response body"),
            (0, json.dumps(MOCK_SERVERS_GET_RESPONSE), "MOCKED response body")
                ]
        backlog = fault_vm.buildBacklog_fault_vm(vimid="windriver-hudson-dc_RegionOne",
                                                        backlog_input = MOCK_BACKLOG_INPUT_wo_server_id)
        self.assertIsNotNone(backlog)
        pass

    @mock.patch.object(restcall, '_call_req')
    def test_buildBacklog_fault_vm_wo_server(self, mock_call_req):

        mock_call_req.side_effect= [
            (0, json.dumps(MOCK_TOKEN_RESPONSE), "MOCKED response body"),
            (0, json.dumps(MOCK_SERVERS_GET_RESPONSE), "MOCKED response body")
                ]
        backlog = fault_vm.buildBacklog_fault_vm(vimid="windriver-hudson-dc_RegionOne",
                                                        backlog_input = MOCK_BACKLOG_INPUT_wo_server)
        self.assertIsNotNone(backlog)
        pass

    @mock.patch.object(vespublish, 'publishAnyEventToVES')
    @mock.patch.object(restcall, '_call_req')
    def test_processBacklog_fault_vm(self, mock_call_req, mock_publishAnyEventToVES):

        mock_call_req.side_effect= [
            (0, json.dumps(MOCK_TOKEN_RESPONSE), "MOCKED response body"),
            (0, json.dumps(MOCK_SERVER_GET_RESPONSE), "MOCKED response body")
                ]
        mock_publishAnyEventToVES.return_value = "mocked return value"

        result = fault_vm.processBacklog_fault_vm(vesAgentConfig=MOCK_vesAgentConfig,
                                                   vesAgentState=MOCK_vesAgentState,
                                                   oneBacklog=MOCK_oneBacklog)
        self.assertIsNone(result)
        pass

    @mock.patch.object(vespublish, 'publishAnyEventToVES')
    @mock.patch.object(restcall, '_call_req')
    def test_processBacklog_fault_vm_wo_server(self, mock_call_req, mock_publishAnyEventToVES):

        mock_call_req.side_effect= [
            (0, json.dumps(MOCK_TOKEN_RESPONSE), "MOCKED response body"),
            (0, json.dumps(MOCK_SERVER_GET_RESPONSE_empty), "MOCKED response body")
                ]
        mock_publishAnyEventToVES.return_value = "mocked return value"

        result = fault_vm.processBacklog_fault_vm(vesAgentConfig=MOCK_vesAgentConfig,
                                                   vesAgentState=MOCK_vesAgentState,
                                                   oneBacklog=MOCK_oneBacklog)
        self.assertIsNone(result)
        pass
