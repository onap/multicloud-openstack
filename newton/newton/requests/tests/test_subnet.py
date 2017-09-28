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

from newton.requests.tests import test_base
from newton.requests.tests import mock_info
from newton.requests.views.util import VimDriverUtils


MOCK_GET_SUBNETS_RESPONSE = {
    "subnets": [
        {"id": "uuid_1", "name": "subnet_1"},
        {"id": "uuid_2", "name": "subnet_2"}
    ]
}

MOCK_GET_SUBNET_RESPONSE = {
    "subnet": {
        "id": "uuid_1",
        "name": "subnet_1"
    }
}

MOCK_GET_SUBNET_RESPONSE_NOT_FOUND = {
    "subnet": {}
}

MOCK_POST_SUBNET_REQUEST = {
    "id": "uuid_3",
    "name": "subnet_3",
}

MOCK_POST_SUBNET_REQUEST_EXISTING = {
    "id": "uuid_1",
    "name": "subnet_1",
}

MOCK_POST_SUBNET_RESPONSE = {
    "subnet": {
        "id": "uuid_3",
        "name": "subnet_3"
    }
}


class TestSubnet(unittest.TestCase):
    def setUp(self):
        self.client = Client()

    def tearDown(self):
        pass

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_get_subnets(self, mock_get_vim_info, mock_get_session):
        mock_get_session.side_effect = [
            test_base.get_mock_session(
                ["get"],
                {"get": {"content": MOCK_GET_SUBNETS_RESPONSE}})
        ]
        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        response = self.client.get(
            "/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne/fcca3cc49d5e42caae15459e27103efc/subnets",
            {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        context = response.json()
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertIsNotNone(context['subnets'])
        self.assertEqual(MOCK_GET_SUBNETS_RESPONSE["subnets"], context["subnets"])

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_get_subnet(self, mock_get_vim_info, mock_get_session):
        mock_get_session.side_effect = [
            test_base.get_mock_session(
                ["get"],
                {"get": {"content": MOCK_GET_SUBNET_RESPONSE}})
        ]
        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        response = self.client.get(
            "/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne/fcca3cc49d5e42caae15459e27103efc/subnets"
            "/uuid_1",
            {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        context = response.json()
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertEqual(MOCK_GET_SUBNET_RESPONSE["id"], context["id"])

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_get_subnet_not_found(self, mock_get_vim_info, mock_get_session):
        mock_get_session.side_effect = [
            test_base.get_mock_session(
                ["get"],
                {"get": {"content": MOCK_GET_SUBNET_RESPONSE_NOT_FOUND,
                         "status_code": 404}}),
        ]
        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        response = self.client.get(
            "/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne/fcca3cc49d5e42caae15459e27103efc/subnets"
            "/uuid_3",
            {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        context = response.json()
        self.assertEquals(status.HTTP_404_NOT_FOUND, response.status_code)
        self.assertIsNone(context.get("subnet"))

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_create_subnet_success(self, mock_get_vim_info, mock_get_session):
        mock_get_session.side_effect = [
            test_base.get_mock_session(
                ["get"],
                {"get": {"content": MOCK_GET_SUBNETS_RESPONSE}}),
            test_base.get_mock_session(
                ["post"],
                {"post": {"content": MOCK_POST_SUBNET_RESPONSE,
                          "status_code": 201}})
        ]
        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        response = self.client.post(
            "/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne/fcca3cc49d5e42caae15459e27103efc/subnets",
            MOCK_POST_SUBNET_REQUEST, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)
        context = response.json()

        self.assertEquals(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(MOCK_POST_SUBNET_RESPONSE["subnet"], context)

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_create_subnet_fail_existing(self, mock_get_vim_info, mock_get_session):
        mock_get_session.side_effect = [
            test_base.get_mock_session(
                ["get"],
                {"get": {"content": MOCK_GET_SUBNETS_RESPONSE}}),
            test_base.get_mock_session(
                ["post"],
                {"post": {"content": MOCK_POST_SUBNET_RESPONSE,
                          "status_code": 404}})
        ]
        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        response = self.client.post(
            "/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne/fcca3cc49d5e42caae15459e27103efc/subnets",
            MOCK_POST_SUBNET_REQUEST_EXISTING, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)
        context = response.json()

        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertIsNotNone(context['returnCode'])
        self.assertEqual(0, context['returnCode'])

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_delete_subnet_success(self, mock_get_vim_info, mock_get_session):
        mock_get_session.side_effect = [
            test_base.get_mock_session(
                ["delete"],
                {"delete": {"content": None,
                            "status_code": 204}})
        ]
        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        response = self.client.delete(
            "/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne/fcca3cc49d5e42caae15459e27103efc/subnets"
            "/uuid_1", HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertIsNone(response.data)
