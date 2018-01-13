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

MOCK_GET_VPORTS_RESPONSE = {
    "ports": [
        {"id": "uuid_1", "name": "vport_1"},
        {"id": "uuid_2", "name": "vport_2"}
    ]
}

MOCK_GET_VPORT_RESPONSE = {
    "port": {
        "id": "uuid_1",
        "name": "vport_1"
    }
}

MOCK_POST_VPORT_REQUEST = {
    "id": "uuid_3",
    "name": "vport_3"
}

MOCK_POST_VPORT_REQUEST_EXISTING = {
    "id": "uuid_1",
    "name": "vport_1"
}

MOCK_POST_VPORT_RESPONSE = {
    "port": {
        "id": "uuid_3",
        "name": "vport_3"
    }
}

class Testvports(test_base.TestRequest):

    url = ("/api/%s/v0/windriver-hudson-dc_RegionOne/"
           "fcca3cc49d5e42caae15459e27103efc/" % test_base.MULTIVIM_VERSION)
    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_get_vports(self, mock_get_vim_info, mock_get_session):

        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO
        mock_get_session.return_value = test_base.get_mock_session(
            ["get"],
            {"get": {"content": MOCK_GET_VPORTS_RESPONSE}})

        response = self.client.get(
            self.url + "ports",
            {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        context = response.json()
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertIsNotNone(context['ports'])
        self.assertEqual(MOCK_GET_VPORTS_RESPONSE["ports"], context['ports'])

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_get_vport(self, mock_get_vim_info, mock_get_session):

        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO
        mock_get_session.return_value = test_base.get_mock_session(
            ["get"],
            {"get": {"content": MOCK_GET_VPORT_RESPONSE}})

        response = self.client.get(
            self.url + "ports/uuid_1",
            {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        context = response.json()
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertEquals(MOCK_GET_VPORT_RESPONSE['id'], context['id'])

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_get_vport_not_found(self, mock_get_vim_info, mock_get_session):

        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO
        mock_get_session.return_value = test_base.get_mock_session(
            ["get"],
            {"get": {"content": None, "status_code": status.HTTP_404_NOT_FOUND}})

        response = self.client.get(
            self.url + "ports/uuid_3",
            {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        self.assertEquals(status.HTTP_500_INTERNAL_SERVER_ERROR, response.status_code)
        self.assertIn('error', response.data)

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_create_vport_successfully(self, mock_get_vim_info, mock_get_session):

        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO
        mock_get_session.return_value = test_base.get_mock_session(
            ["get", "post"],
            {
             "get" : {"content": MOCK_GET_VPORTS_RESPONSE},
             "post": {"content": MOCK_POST_VPORT_RESPONSE,
                      "status_code": status.HTTP_202_ACCEPTED}
            })

        response = self.client.post(
            self.url + "ports",
            MOCK_POST_VPORT_REQUEST, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        context = response.json()
        self.assertEquals(status.HTTP_202_ACCEPTED, response.status_code)
        self.assertIsNotNone(context['id'])
        self.assertEqual(1, context['returnCode'])

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_create_existing_vport(self, mock_get_vim_info, mock_get_session):

        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO
        mock_get_session.return_value = test_base.get_mock_session(
            ["get", "post"],
            {
             "get" : {"content": MOCK_GET_VPORTS_RESPONSE},
             "post": {"content": MOCK_POST_VPORT_RESPONSE,
                      "status_code": status.HTTP_202_ACCEPTED}
            })

        response = self.client.post(
            self.url + "ports",
            MOCK_POST_VPORT_REQUEST_EXISTING, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        context = response.json()
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertIsNotNone(context['returnCode'])
        self.assertEqual(0, context['returnCode'])

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_create_vport_unsuccessfully(self, mock_get_vim_info, mock_get_session):

        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO
        mock_get_session.return_value = test_base.get_mock_session(
            ["get", "post"],
            {
             "get" : {"content": MOCK_GET_VPORTS_RESPONSE},
             "post": {"content": MOCK_POST_VPORT_RESPONSE,
                      "status_code": status.HTTP_202_ACCEPTED}
            })

        response = self.client.post(
            self.url + "ports",
            {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        context = response.json()
        self.assertIn('error', context)
        self.assertEquals(status.HTTP_500_INTERNAL_SERVER_ERROR, response.status_code)

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_delete_vport(self, mock_get_vim_info, mock_get_session):

        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO
        mock_get_session.return_value = test_base.get_mock_session(
            ["delete"],
            {"delete" : {"content": None,
                         "status_code": status.HTTP_204_NO_CONTENT}})

        response = self.client.delete(
            self.url + "ports/uuid_1",
            HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertIsNone(response.data)

