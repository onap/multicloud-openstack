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
from django.test import Client
from rest_framework import status

from django.core.cache import cache
from common.msapi import extsys
from titanium_cloud.vesagent import vesagent_ctrl
from titanium_cloud.vesagent.event_domain import fault_vm



MOCK_VIM_INFO = {
    "createTime": "2017-04-01 02:22:27",
    "domain": "Default",
    "name": "TiS_R4",
    "password": "admin",
    "tenant": "admin",
    "type": "openstack",
    "url": "http://128.224.180.14:5000/v3",
    "userName": "admin",
    "vendor": "WindRiver",
    "version": "newton",
    "vimId": "windriver-hudson-dc_RegionOne",
    'cloud_owner': 'windriver-hudson-dc',
    'cloud_region_id': 'RegionOne',
    'cloud_extra_info': '{"vesagent_config":{"backlogs":[{"source":"onap-aaf","domain":"fault","type":"vm","tenant":"VIM"}],"poll_interval_default":10,"ves_subscription":{"username":"user","password":"password","endpoint":"http://127.0.0.1:9005/sample"}}}',
    'cloud_epa_caps': '',
    'insecure': 'True',
}


class VesAgentCtrlTest(unittest.TestCase):
    def setUp(self):
        self.client = Client()
        self.view = vesagent_ctrl.VesAgentCtrl()

    def tearDown(self):
        pass

    @mock.patch.object(cache, 'get')
    @mock.patch.object(extsys, 'get_vim_by_id')
    def test_get(self, mock_get_vim_by_id, mock_get):
        mock_get_vim_by_id.return_value = MOCK_VIM_INFO
        mock_get.return_value = '{"backlogs": [{"backlog_uuid": "2b8f6ff8-bc64-339b-a714-155909db937f", "server_id": "c4b575fa-ed85-4642-ab4b-335cb5744721", "tenant_id": "0e148b76ee8c42f78d37013bf6b7b1ae", "api_method": "GET", "source": "onap-aaf", "api_link": "/onaplab_RegionOne/compute/v2.1/0e148b76ee8c42f78d37013bf6b7b1ae/servers/c4b575fa-ed85-4642-ab4b-335cb5744721", "domain": "fault", "type": "vm", "tenant": "VIM"}], "poll_interval_default": 10, "vimid": "onaplab_RegionOne", "subscription": {"username": "user", "password": "password", "endpoint": "http://127.0.0.1:9005/sample"}}'

        response = self.client.get("/api/multicloud-titanium_cloud/v0/windriver-hudson-dc_RegionOne/vesagent")
        self.assertEqual(status.HTTP_200_OK, response.status_code, response.content)

    @mock.patch.object(vesagent_ctrl.VesAgentCtrl, 'buildBacklogsOneVIM')
    @mock.patch.object(extsys, 'get_vim_by_id')
    def test_post(self, mock_get_vim_by_id, mock_buildBacklogsOneVIM):
        mock_get_vim_by_id.return_value = MOCK_VIM_INFO
        mock_buildBacklogsOneVIM.return_value = "mocked vesagent_backlogs"
        mock_request = mock.Mock()
        mock_request.META = {"testkey":"testvalue"}
        mock_request.data = {"testdatakey":"testdatavalue"}

        response = self.view.post(request=mock_request, vimid="windriver-hudson-dc_RegionOne")
        self.assertEquals(status.HTTP_201_CREATED, response.status_code)

        pass

    @mock.patch.object(vesagent_ctrl.VesAgentCtrl, 'clearBacklogsOneVIM')
    @mock.patch.object(extsys, 'get_vim_by_id')
    def test_delete(self, mock_get_vim_by_id, mock_clearBacklogsOneVIM):
        mock_get_vim_by_id.return_value = MOCK_VIM_INFO
        mock_clearBacklogsOneVIM.return_value = "mocked vesagent_backlogs"
        mock_request = mock.Mock()
        mock_request.META = {"testkey": "testvalue"}

        response = self.view.delete(request=mock_request, vimid="windriver-hudson-dc_RegionOne")
        self.assertEquals(status.HTTP_200_OK, response.status_code)

        pass

    @mock.patch.object(cache, 'get')
    def test_getBacklogsOneVIM(self, mock_get):
        mock_vesagent_config = {"backlogs": [{"backlog_uuid": "ce2d7597-22e1-4239-890f-bc303bd67076", "server_id": "c4b575fa-ed85-4642-ab4b-335cb5744721", "tenant_id": "0e148b76ee8c42f78d37013bf6b7b1ae", "api_method": "GET", "source": "onap-aaf", "api_link": "/onaplab_RegionOne/compute/v2.1/0e148b76ee8c42f78d37013bf6b7b1ae/servers/c4b575fa-ed85-4642-ab4b-335cb5744721", "domain": "fault", "type": "vm", "tenant": "VIM"}], "poll_interval_default": 10, "vimid": "onaplab_RegionOne", "subscription": {"username": "user", "password": "password", "endpoint": "http://127.0.0.1:9005/sample"}}
        mock_get.return_value = json.dumps(mock_vesagent_config)

        vesAgentConfig = self.view.getBacklogsOneVIM(vimid="windriver-hudson-dc_RegionOne")
        self.assertEquals(vesAgentConfig, mock_vesagent_config)

        pass

    @mock.patch.object(cache, 'set')
    @mock.patch.object(cache, 'get')
    def test_clearBacklogsOneVIM(self, mock_get, mock_set):
        mock_VesAgentBacklogs_vimlist = ["windriver-hudson-dc_RegionOne"]
        mock_vesagent_config = {"backlogs": [{"backlog_uuid": "ce2d7597-22e1-4239-890f-bc303bd67076",
                                              "server_id": "c4b575fa-ed85-4642-ab4b-335cb5744721",
                                              "tenant_id": "0e148b76ee8c42f78d37013bf6b7b1ae", "api_method": "GET",
                                              "source": "onap-aaf",
                                              "api_link": "/onaplab_RegionOne/compute/v2.1/0e148b76ee8c42f78d37013bf6b7b1ae/servers/c4b575fa-ed85-4642-ab4b-335cb5744721",
                                              "domain": "fault", "type": "vm", "tenant": "VIM"}],
                                "poll_interval_default": 10, "vimid": "onaplab_RegionOne",
                                "subscription": {"username": "user", "password": "password",
                                                 "endpoint": "http://127.0.0.1:9005/sample"}}

        mock_get.side_effect= [
                    json.dumps(mock_VesAgentBacklogs_vimlist),
                    json.dumps(mock_vesagent_config)
                ]


        mock_set.return_value = "mocked cache set"

        result = self.view.clearBacklogsOneVIM(vimid="windriver-hudson-dc_RegionOne")
        self.assertEquals(0, result)

        pass

    from titanium_cloud.vesagent.tasks import scheduleBacklogs

    @mock.patch.object(scheduleBacklogs, 'delay')
    @mock.patch.object(cache, 'set')
    @mock.patch.object(cache, 'get')
    def test_buildBacklogsOneVIM(self, mock_get, mock_set, mock_scheduleBacklogs_delay):
        mock_VesAgentBacklogs_vimlist = ["windriver-hudson-dc_RegionOne"]
        mock_vesagent_config = {"backlogs": [{"backlog_uuid": "ce2d7597-22e1-4239-890f-bc303bd67076",
                                              "server_id": "c4b575fa-ed85-4642-ab4b-335cb5744721",
                                              "tenant_id": "0e148b76ee8c42f78d37013bf6b7b1ae", "api_method": "GET",
                                              "source": "onap-aaf",
                                              "api_link": "/onaplab_RegionOne/compute/v2.1/0e148b76ee8c42f78d37013bf6b7b1ae/servers/c4b575fa-ed85-4642-ab4b-335cb5744721",
                                              "domain": "fault", "type": "vm", "tenant": "VIM"}],
                                "poll_interval_default": 10, "vimid": "windriver-hudson-dc_RegionOne",
                                "ves_subscription": {"username": "user", "password": "password",
                                                 "endpoint": "http://127.0.0.1:9005/sample"}}

        mock_get.side_effect= [
                    json.dumps(mock_VesAgentBacklogs_vimlist),
                ]

        mock_set.return_value = "mocked cache set"
        mock_scheduleBacklogs_delay.return_value = "mocked delay"

        VesAgentBacklogsConfig = self.view.buildBacklogsOneVIM(vimid="windriver-hudson-dc_RegionOne",
                                                               vesagent_config = mock_vesagent_config)
        self.assertIsNotNone(VesAgentBacklogsConfig)

        pass


    @mock.patch.object(fault_vm, 'buildBacklog_fault_vm')
    def test_buildBacklog(self, mock_buildBacklog_fault_vm):
        mock_backlog_input = {"backlog_uuid": "ce2d7597-22e1-4239-890f-bc303bd67076",
                                              "server_id": "c4b575fa-ed85-4642-ab4b-335cb5744721",
                                              "tenant_id": "0e148b76ee8c42f78d37013bf6b7b1ae", "api_method": "GET",
                                              "source": "onap-aaf",
                                              "api_link": "/onaplab_RegionOne/compute/v2.1/0e148b76ee8c42f78d37013bf6b7b1ae/servers/c4b575fa-ed85-4642-ab4b-335cb5744721",
                                              "domain": "fault", "type": "vm", "tenant": "VIM"}


        mock_buildBacklog_fault_vm.return_value = "mocked buildBacklog_fault_vm"

        VesAgentBacklogsConfig = self.view.buildBacklog(vimid="windriver-hudson-dc_RegionOne",
                                                        backlog_input = mock_backlog_input)
        self.assertIsNotNone(VesAgentBacklogsConfig)

        pass
