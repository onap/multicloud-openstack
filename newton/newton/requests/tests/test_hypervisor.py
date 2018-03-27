# -*- coding: UTF-8 -*-
# Copyright (c) 2018, CMCC Technologies Co., Ltd.
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

from rest_framework import status

from newton_base.tests import mock_info
from newton_base.tests import test_base
from newton_base.tests.test_base import AbstractTestResource
from newton_base.util import VimDriverUtils


class TestHypervisor(unittest.TestCase, AbstractTestResource):

    def setUp(self):
        AbstractTestResource.__init__(self)

        self.url += "hypervisors"

        self.MOCK_GET_RESOURCES_RESPONSE = {
            "hypervisors": [
                {"id": "uuid_1", "name": "hypervisor_1"},
                {"id": "uuid_2", "name": "hypervisor_2"}
            ]
        }

        self.MOCK_GET_RESOURCE_RESPONSE_NOT_FOUND = {}

        self.assert_keys = "hypervisors"

        self.HTTP_not_found = status.HTTP_404_NOT_FOUND

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_get_hypervisors(self, mock_get_vim_info, mock_get_session):
        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO
        mock_get_session.return_value = test_base.get_mock_session(
            ["get"],
            {"get": {"content": self.MOCK_GET_RESOURCES_RESPONSE}})

        response = self.client.get(
            "/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne/fcca3cc49d5e42caae15459e27103efc/"
            "hypervisors", {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        context = response.json()
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertIsNotNone(context["hypervisors"])
        self.assertEqual(self.MOCK_GET_RESOURCES_RESPONSE["hypervisors"], context["hypervisors"])

    # Overridden method from test base to not make it run for current test case.
    def test_get_resource_info(self):
        pass

    def test_get_resources_list(self):
        pass

    def test_post_resource(self):
        pass

    def test_post_resource_empty(self):
        pass

    def test_post_resource_existing(self):
        pass

    def test_delete_resource(self):
        pass
