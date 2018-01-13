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

from newton.requests.tests import mock_info
from newton.requests.tests import test_base
from newton.requests.views.util import VimDriverUtils

MOCK_GET_PROJECTS_RESPONSE = {
    "tenants": [
        {"id": "1", "name": "project"},
        {"id": "2", "name": "project2"},
    ]
}


class TestNetwork(test_base.TestRequest):
    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_retrieve_projects(
            self, mock_get_vim_info, mock_get_session):
        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO
        mock_get_session.side_effect = [
            test_base.get_mock_session(
                ["get"],
                {"get": {"content": MOCK_GET_PROJECTS_RESPONSE}}),
        ]

        response = self.client.get((
            "/api/%s/v0/windriver-hudson-dc_RegionOne/"
            "tenants" % test_base.MULTIVIM_VERSION), {},
            HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        self.assertEquals(status.HTTP_200_OK, response.status_code)
        content = response.json()
        self.assertIsNotNone(content["tenants"])
        self.assertEquals(
            len(MOCK_GET_PROJECTS_RESPONSE["tenants"]),
            len(content["tenants"])
        )
        self.assertEquals(mock_info.MOCK_VIM_INFO["name"],
                          content["vimName"])
        self.assertEquals(mock_info.MOCK_VIM_INFO["vimId"],
                          content["vimId"])

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_retrieve_projects_by_querystring(
            self, mock_get_vim_info, mock_get_session):
        mock_vim_identity_v2 = mock_info.MOCK_VIM_INFO.copy()
        mock_vim_identity_v2["url"] = "http://128.224.180.14:5000/v2"
        mock_get_vim_info.return_value = mock_vim_identity_v2
        mock_get_session.side_effect = [
            test_base.get_mock_session(
                ["get"],
                {"get": {"content": MOCK_GET_PROJECTS_RESPONSE}}),
        ]

        response = self.client.get((
            "/api/%s/v0/windriver-hudson-dc_RegionOne/"
            "tenants?name=project" % test_base.MULTIVIM_VERSION), {},
            HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        self.assertEquals(status.HTTP_200_OK, response.status_code)
