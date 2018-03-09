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

from rest_framework import status

from newton_base.tests import test_base
from newton_base.tests import mock_info
from newton_base.tests.test_base import AbstractTestResource
from newton_base.util import VimDriverUtils


class TestSubnetNewton(unittest.TestCase, AbstractTestResource):
    def setUp(self):
        AbstractTestResource.__init__(self)

        self.url += "subnets"

        self.MOCK_GET_RESOURCES_RESPONSE = {
            "subnets": [
                {"id": "uuid_1", "name": "subnet_1"},
                {"id": "uuid_2", "name": "subnet_2"}
            ]
        }

        self.MOCK_GET_RESOURCE_RESPONSE = {
            "subnet": {
                "id": "uuid_1",
                "name": "subnet_1"
            }
        }

        self.MOCK_GET_RESOURCE_RESPONSE_NOT_FOUND = {
            "subnet": {}
        }

        self.MOCK_POST_RESOURCE_REQUEST = {
            "id": "uuid_3",
            "name": "subnet_3"
        }

        self.MOCK_POST_RESOURCE_REQUEST_EXISTING = {
            "id": "uuid_1",
            "name": "subnet_1"
        }

        self.MOCK_POST_RESOURCE_RESPONSE = {
            "subnet": {
                "id": "uuid_3",
                "name": "subnet_3"
            }
        }

        self.assert_keys = "subnets"
        self.assert_key = "subnet"

        self.HTTP_not_found = status.HTTP_404_NOT_FOUND

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_get_subnet(self, mock_get_vim_info, mock_get_session):
        mock_get_session.side_effect = [
            test_base.get_mock_session(
                ["get"],
                {"get": {"content": self.MOCK_GET_RESOURCE_RESPONSE}})
        ]
        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        response = self.client.get(
            "/api/%s/v0/windriver-hudson-dc_RegionOne/"
            "fcca3cc49d5e42caae15459e27103efc/subnets/"
            "uuid_1" % test_base.MULTIVIM_VERSION,
            {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        context = response.json()
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertEqual(self.MOCK_GET_RESOURCE_RESPONSE["id"],
                         context["id"])

    # Overridden method from test base to not make it run for current test case.
    def test_get_resource_info(self):
        pass
