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
import unittest

from django.test import Client
from rest_framework import status

from newton.requests.tests import mock_info
from newton.requests.tests import test_base
from newton.requests.views.util import VimDriverUtils


MOCK_GET_HOSTS_RESPONSE = {
    "hosts": [
        {"id": "uuid_1", "name": "host_1"},
        {"id": "uuid_2", "name": "host_2"}
    ]
}

MOCK_GET_HOST_RESPONSE = {
    "host": [
        {"resource": {"id": "uuid_1", "name": "host_1"}}
    ]
}


class TestHost(unittest.TestCase):
    def setUp(self):
        self.client = Client()
    def tearDown(self):
        pass

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_get_hosts_list(self, mock_get_vim_info, mock_get_session):
        mock_get_session.side_effect = [
            test_base.get_mock_session(
                ["get"], {"get": {"content": MOCK_GET_HOSTS_RESPONSE}}),
        ]

        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        response = self.client.get(
            "/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne/fcca3cc49d5e42caae15459e27103efc/hosts",
            {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        context = response.json()
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertIsNotNone(context['hosts'])
        self.assertEqual(MOCK_GET_HOSTS_RESPONSE["hosts"], context["hosts"])

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_get_host_info(self, mock_get_vim_info, mock_get_session):
        mock_get_session.side_effect = [
            test_base.get_mock_session(
                ["get"], {"get": {"content": MOCK_GET_HOST_RESPONSE}}),
        ]

        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        response = self.client.get(
            "/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne/fcca3cc49d5e42caae15459e27103efc/hosts"
            "/uuid_1",
            {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        context = response.json()
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertEquals(MOCK_GET_HOST_RESPONSE['host'], context['host'])

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_get_host_not_found(self, mock_get_vim_info, mock_get_session):
        mock_get_session.side_effect = [
            test_base.get_mock_session(
                ["get"], {"get": {"content": {},
                                  "status_code": 404}}),
        ]

        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        response = self.client.get(
            "/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne/fcca3cc49d5e42caae15459e27103efc/hosts"
            "/uuid_3",
            {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        self.assertEquals(status.HTTP_500_INTERNAL_SERVER_ERROR, response.status_code)
        self.assertIn('error', response.data)
