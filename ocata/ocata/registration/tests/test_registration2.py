# Copyright (c) 2018 Intel Corporation.
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

from common.utils import restcall
from newton_base.tests import mock_info
from newton_base.tests import test_base
from newton_base.util import VimDriverUtils

from newton_base.registration import registration as newton_registration
from ocata.registration.views import registration
from newton_base.tests import test_base

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
    'cloud_extra_info': '',
    'insecure': 'True',
}

MOCK_GET_FLAVOR_RESPONSE = {
    "flavors": [
        {
            "id": "1", "name": "micro", "vcpus": 1, "ram": "1MB",
            "disk": "1G", "OS-FLV-EXT-DATA:ephemeral": False,
            "swap": True, "os-flavor-access:is_public": True,
            "OS-FLV-DISABLED:disabled": True, "link": [{"href":1}]
         },
        {
            "id": "2", "name": "mini", "vcpus": 2, "ram": "2MB",
            "disk": "2G", "OS-FLV-EXT-DATA:ephemeral": True,
            "swap": False, "os-flavor-access:is_public": True,
            "OS-FLV-DISABLED:disabled": True
        },
    ]
}

MOCK_GET_FLAVOR_RESPONSE_w_hpa_numa = {
    "flavors": [
        {
            "id": "1", "name": "onap.big", "vcpus": 6, "ram": "8192",
            "disk": "10", "OS-FLV-EXT-DATA:ephemeral": False,
            "swap": True, "os-flavor-access:is_public": True,
            "OS-FLV-DISABLED:disabled": True, "link": [{"href":1}]
         }
    ]
}
MOCK_GET_FLAVOR_EXTRASPECS_RESPONSE_w_hpa_numa = {
    "hw:numa_nodes": 2
}

class TestRegistration2(unittest.TestCase):
    def setUp(self):
        self.client = Client()
        self.view = registration.Registry()

    def tearDown(self):
        pass


    def test_discover_flavors(self):
        restcall.req_to_aai = mock.Mock()
        restcall.req_to_aai.return_value = (0, {}, status.HTTP_200_OK)
        mock_session =  test_base.get_mock_session(
                ["get"], {"get": {
                    "content": MOCK_GET_FLAVOR_RESPONSE}}),

        resp = self.view._discover_flavors(vimid="windriver-hudson-dc_RegionOne",
                                           session=mock_session, viminfo=MOCK_VIM_INFO)

        self.assertIsNone(resp)

    def test_discover_flavors_w_hpa_numa(self):
        restcall.req_to_aai = mock.Mock()
        restcall.req_to_aai.return_value = (0, {}, status.HTTP_200_OK)
        mock_session = test_base.get_mock_session(
                ["get"], {"side_effect": [{
                    "content": MOCK_GET_FLAVOR_RESPONSE_w_hpa_numa},
                {
                    "content": MOCK_GET_FLAVOR_EXTRASPECS_RESPONSE_w_hpa_numa}
            ]}),

        resp = self.view._discover_flavors(vimid="windriver-hudson-dc_RegionOne",
                                           session=mock_session, viminfo=MOCK_VIM_INFO)

        self.assertIsNone(resp)
