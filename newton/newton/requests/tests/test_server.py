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

import json

import mock
from rest_framework import status

from newton.requests.tests import mock_info
from newton.requests.tests import test_base
from newton.requests.views.util import VimDriverUtils

MOCK_GET_SERVERS_RESPONSE = {
    "servers": [
        {
            "name": "compute_1",
            "id": "1"
        },
        {
            "name": "compute_2",
            "id": "2"
        }
    ]
}

MOCK_GET_SERVER_RESPONSE = {
    "server":
        {
            "name": "compute_1",
            "id": "1"
        }
}

MOCK_GET_PORTS_RESPONSE = {
    "interfaceAttachments": [
        {
            "port_id": "1",
        },
        {
            "port_id": "2",
        },
    ]
}

TEST_CREATE_SERVER = {
    "name": "compute_1",
    "boot": {
        "type": 1,
        "volumeId": "1"
    },
    "nicArray": [
        {"portId": "1"},
        {"portId": "2"}
    ],
    "contextArray": [
        {"fileName": "file", "fileData": "test_data"},
        {"fileName": "file2", "fileData": "test_data2"}
    ],
    # "volumeArray":[
    #     {"volumeId": "volume1"},
    # ]
}

MOCK_POST_SERVER_RESPONSE = {
    "server": {
        "id": 1
    }
}

MOCK_POST_SERVER_CREATED_THREAD_RESPONSE = {
    "server": {
        "status": "ACTIVE"
    }
}


class TestNetwork(test_base.TestRequest):
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_get_servers_failure(self, mock_get_vim_info):
        mock_get_vim_info.raiseError.side_effect = mock.Mock(
            side_effect=Exception('Test'))
        tenant_id = "fcca3cc49d5e42caae15459e27103efc"

        response = self.client.get((
            "/api/%s/v0/windriver-hudson-dc_RegionOne/%s/"
            "servers" % (test_base.MULTIVIM_VERSION, tenant_id)),
            {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        self.assertEquals(status.HTTP_500_INTERNAL_SERVER_ERROR,
                          response.status_code)
        content = response.json()

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_get_list_servers(self, mock_get_vim_info,
                              mock_get_session):
        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO
        mock_get_session.side_effect = [
            test_base.get_mock_session(
                ["get"],
                {"get": {"content": MOCK_GET_SERVERS_RESPONSE}}),
            test_base.get_mock_session(
                ["get"],
                {"get": {"content": MOCK_GET_PORTS_RESPONSE}}),
            test_base.get_mock_session(
                ["get"],
                {"get": {"content": None}}),
        ]
        tenant_id = "fcca3cc49d5e42caae15459e27103efc"

        response = self.client.get((
            "/api/%s/v0/windriver-hudson-dc_RegionOne/%s/"
            "servers" % (test_base.MULTIVIM_VERSION, tenant_id)),
            {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        self.assertEquals(status.HTTP_200_OK, response.status_code)
        content = response.json()
        self.assertEquals(
            mock_info.MOCK_VIM_INFO["name"], content["vimName"])
        self.assertEquals(tenant_id, content["tenantId"])
        self.assertEquals(
            mock_info.MOCK_VIM_INFO["vimId"], content["vimId"])
        self.assertEquals(len(MOCK_GET_SERVERS_RESPONSE["servers"]),
                          len(content["servers"]))

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_one_server_info(self, mock_get_vim_info,
                             mock_get_session):
        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO
        mock_get_session.side_effect = [
            test_base.get_mock_session(
                ["get"], {"get": {
                    "content": MOCK_GET_SERVER_RESPONSE.copy()}}),
            test_base.get_mock_session(
                ["get"], {"get": {
                    "content": MOCK_GET_PORTS_RESPONSE.copy()}}),
        ]
        tenant_id = "fcca3cc49d5e42caae15459e27103efc"
        server_id = "f5dc173b-6804-445a-a6d8-c705dad5b5eb"

        response = self.client.get((
            "/api/%s/v0/windriver-hudson-dc_RegionOne/%s/"
            "servers/%s" % (test_base.MULTIVIM_VERSION,
                            tenant_id, server_id)),
            {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        self.assertEquals(status.HTTP_200_OK, response.status_code)
        content = response.json()
        self.assertEquals(
            mock_info.MOCK_VIM_INFO["name"], content["vimName"])
        self.assertEquals(tenant_id, content["tenantId"])
        self.assertEquals(
            mock_info.MOCK_VIM_INFO["vimId"], content["vimId"])

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_create_existing_server(self, mock_get_vim_info,
                                    mock_get_session):
        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO
        mock_get_session.side_effect = [
            test_base.get_mock_session(
                ["get"],
                {"get": {"content": MOCK_GET_SERVERS_RESPONSE}}),
            test_base.get_mock_session(
                ["get"], {"get": {"content": None}}),
            test_base.get_mock_session(
                ["get"], {"get": {"content": None}}),
        ]

        tenant_id = "fcca3cc49d5e42caae15459e27103efc"
        server_id = "f5dc173b-6804-445a-a6d8-c705dad5b5eb"

        response = self.client.post((
            "/api/%s/v0/windriver-hudson-dc_RegionOne/%s/"
            "servers/%s" % (test_base.MULTIVIM_VERSION, tenant_id,
                            server_id)),
            data=json.dumps(TEST_CREATE_SERVER),
            content_type="application/json",
            HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        context = response.json()
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertIsNone(context["volumeArray"])
        self.assertIsNone(context["flavorId"])
        self.assertIsNone(context["availabilityZone"])
        self.assertEquals(TEST_CREATE_SERVER["name"], context["name"])
        self.assertEquals(
            MOCK_GET_SERVERS_RESPONSE["servers"][0]["id"],
            context["id"])
        self.assertIsNone(context["nicArray"])
        self.assertIsNotNone(context["boot"])
        self.assertEquals(0, context["returnCode"])

    @mock.patch.object(VimDriverUtils, 'get_session')
    def test_create_server_successfully(self, mock_get_session):
        VimDriverUtils.get_vim_info = mock.Mock(
            return_value=mock_info.MOCK_VIM_INFO)

        mock_get_session.side_effect = [
            test_base.get_mock_session(
                ["get"], {"get": {"content": {"servers": []}}}),
            test_base.get_mock_session(
                ["post"], {"post": {
                    "content": MOCK_POST_SERVER_RESPONSE.copy()}}),
        ]
        tenant_id = "fcca3cc49d5e42caae15459e27103efc"
        server_id = "f5dc173b-6804-445a-a6d8-c705dad5b5eb"

        response = self.client.post((
            "/api/%s/v0/windriver-hudson-dc_RegionOne/%s/"
            "servers/%s" % (test_base.MULTIVIM_VERSION, tenant_id,
                            server_id)),
            data=json.dumps(TEST_CREATE_SERVER),
            content_type="application/json",
            HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        context = response.json()
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertEquals(
            mock_info.MOCK_VIM_INFO["vimId"], context["vimId"])
        self.assertEquals(tenant_id, context["tenantId"])
        # self.assertEquals(len(TEST_CREATE_SERVER["volumeArray"]),
        #                   len(context['volumeArray']))
        self.assertEquals(
            MOCK_POST_SERVER_RESPONSE["server"]["id"], context["id"])
        self.assertEquals(len(TEST_CREATE_SERVER["nicArray"]),
                          len(context["nicArray"]))
        self.assertEquals(
            mock_info.MOCK_VIM_INFO["name"], context["vimName"])
        self.assertIsNotNone(TEST_CREATE_SERVER["boot"])
        self.assertEquals(TEST_CREATE_SERVER["boot"]["volumeId"],
                          context["boot"]["volumeId"])
        self.assertEquals(TEST_CREATE_SERVER["boot"]["type"],
                          context["boot"]["type"])
        self.assertEquals(1, context["returnCode"])
        self.assertEquals(TEST_CREATE_SERVER["name"],
                          context["name"])
        self.assertEquals(
            len(TEST_CREATE_SERVER["contextArray"]),
            len(context["contextArray"]))

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_delete_existing_server(self, mock_get_vim_info,
                                    mock_get_session):
        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO
        mock_get_session.side_effect = [
            test_base.get_mock_session(
                ["delete"], {"delete": {"content": None}}),
            test_base.get_mock_session(
                ["get"],
                {"get": {
                    "content": MOCK_GET_SERVER_RESPONSE.copy()}}),
            test_base.get_mock_session(
                ["get"], {"get": {"content": None}}),
        ]

        tenant_id = "fcca3cc49d5e42caae15459e27103efc"
        server_id = "f5dc173b-6804-445a-a6d8-c705dad5b5eb"

        response = self.client.delete((
            "/api/%s/v0/windriver-hudson-dc_RegionOne/%s/"
            "servers/%s" % (test_base.MULTIVIM_VERSION, tenant_id,
                            server_id)),
            data=json.dumps(TEST_CREATE_SERVER),
            content_type="application/json",
            HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        self.assertEquals(status.HTTP_200_OK, response.status_code)
