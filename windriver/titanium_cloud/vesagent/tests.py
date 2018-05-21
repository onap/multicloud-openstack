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
    'cloud_hpa_caps': '',
    'insecure': 'True',
}

class VesAgentCtrlTest(unittest.TestCase):
    def setUp(self):
        self.client = Client()

    def tearDown(self):
        pass

    @mock.patch.object(cache, 'get')
    @mock.patch.object(extsys, 'get_vim_by_id')
    def test_get(self, mock_get_vim_by_id, mock_get):
        mock_get_vim_by_id.return_value = MOCK_VIM_INFO
        mock_get.return_value = '{"backlogs": [{"backlog_uuid": "2b8f6ff8-bc64-339b-a714-155909db937f", "server_id": "c4b575fa-ed85-4642-ab4b-335cb5744721", "tenant_id": "0e148b76ee8c42f78d37013bf6b7b1ae", "api_method": "GET", "source": "onap-aaf", "api_link": "/onaplab_RegionOne/compute/v2.1/0e148b76ee8c42f78d37013bf6b7b1ae/servers/c4b575fa-ed85-4642-ab4b-335cb5744721", "domain": "fault", "type": "vm", "tenant": "VIM"}], "poll_interval_default": 10, "vimid": "onaplab_RegionOne", "subscription": {"username": "user", "password": "password", "endpoint": "http://127.0.0.1:9005/sample"}}'

        response = self.client.get("/api/multicloud-titanium_cloud/v0/windriver-hudson-dc_RegionOne/vesagent")
        self.assertEqual(status.HTTP_200_OK, response.status_code, response.content)
