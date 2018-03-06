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

import json

import mock
from django.test import Client
from rest_framework import status
import unittest

from newton_base.util import VimDriverUtils

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
    "version": "ocata",
    "vimId": "windriver-hudson-dc_RegionOne",
    'cloud_owner':'windriver-hudson-dc',
    'cloud_region_id':'RegionOne',
    'cloud_extra_info':'',
    'cloud_epa_caps':'{"huge_page":"true","cpu_pinning":"true",\
        "cpu_thread_policy":"true","numa_aware":"true","sriov":"true",\
        "dpdk_vswitch":"true","rdt":"false","numa_locality_pci":"true"}',
    'insecure':'True',
}


class TestEpaCaps(unittest.TestCase):
    def setUp(self):
        self.client = Client()

    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_get_epa_caps_info(self, mock_get_vim_info):
        mock_get_vim_info.return_value = MOCK_VIM_INFO
        cloud_owner = "windriver-hudson-dc"
        cloud_region_id = "RegionOne"
        vimid = cloud_owner + "_" + cloud_region_id

        response = self.client.get(
            "/api/multicloud-ocata/v0/" + vimid + "/extensions/epa-caps")
        json_content = response.json()

        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertEquals(4, len(json_content.keys()))
        self.assertEquals(cloud_owner, json_content["cloud-owner"])
        self.assertEquals(cloud_region_id, json_content["cloud-region-id"])
        self.assertEquals(vimid, json_content["vimid"])
        self.assertEquals(json.loads(MOCK_VIM_INFO['cloud_epa_caps']),
                          json_content["cloud-epa-caps"])
