# Copyright (c) 2017 Intel Corporation, Inc.
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
from rest_framework import status
import unittest

from django.test import Client

MOCK_TOKEN_ID = "1a62b3971d774404a504c5d9a3e506e3"

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
    'cloud_epa_caps': '{"huge_page":"true","cpu_pinning":"true",\
        "cpu_thread_policy":"true","numa_aware":"true","sriov":"true",\
        "dpdk_vswitch":"true","rdt":"false","numa_locality_pci":"true"}',
    'insecure': 'True',
}

class MockResponse(object):
    status_code = status.HTTP_200_OK
    content = ''

    def json(self):
        pass


def get_mock_session(http_actions, response):
    mock_session_specs = http_actions
    mock_session = mock.Mock(
        name='mock_session',spec=mock_session_specs)
    mock_response_obj = mock.Mock(spec=MockResponse)
    mock_response_obj.status_code = status.HTTP_200_OK
    mock_response_obj.content = response
    mock_response_obj.json.return_value = response
    for action in http_actions:
        if action == "get":
            mock_session.get.return_value = mock_response_obj
        if action == "post":
            mock_session.post.return_value = mock_response_obj
        if action == "put":
            mock_session.put.return_value = mock_response_obj
        if action == "delete":
            mock_session.delete.return_value = mock_response_obj
        if action == "head":
            mock_session.head.return_value = mock_response_obj

    return mock_session


class TestRequest(unittest.TestCase):

    def setUp(self):
        self.client = Client()
