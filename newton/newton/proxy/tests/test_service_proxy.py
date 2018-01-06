# Copyright (c) 2017 Wind River Systems, Inc.
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

import copy
import json

from django.test import Client
import mock
from rest_framework import status
import unittest

from newton.requests.tests import mock_info
from newton.requests.tests import test_base
from newton.requests.views.util import VimDriverUtils

MOCK_GET_SERVERS_RESPONSE = {
    "servers": [
        {
            "links": [
                {
                    "href": "http://128.224.180.14:8774/v2.1/"
                            "fcca3cc49d5e42caae15459e27103efc/servers"
                            "/b2581b5c-7c56-4564-819d-fe7a2ce9c261",
                    "rel": "self"
                },
                {
                    "href": "http://128.224.180.14:8774/"
                            "fcca3cc49d5e42caae15459e27103efc/servers"
                            "/b2581b5c-7c56-4564-819d-fe7a2ce9c261",
                    "rel": "bookmark"
                }
            ],
            "id": "b2581b5c-7c56-4564-819d-fe7a2ce9c261",
            "name": "t1"
        },
        {
            "id": "ff7b51ca-a272-45f4-b54c-e40b8099e67d",
            "name": "t2",
            "links": [
                {
                    "rel": "self",
                    "href": "http://128.224.180.14:8774/v2.1/"
                            "fcca3cc49d5e42caae15459e27103efc/servers"
                            "/ff7b51ca-a272-45f4-b54c-e40b8099e67d"
                },
                {
                    "rel": "bookmark",
                    "href": "http://128.224.180.14:8774/"
                            "fcca3cc49d5e42caae15459e27103efc/servers"
                            "/ff7b51ca-a272-45f4-b54c-e40b8099e67d"
                }
            ]
        }
    ]
}

MOCK_POST_SERVER_REQUEST = {
    "server": {
        "accessIPv4": "1.2.3.4",
        "accessIPv6": "80fe::",
        "name": "new-server-test",
        "imageRef": "70a599e0-31e7-49b7-b260-868f441e862b",
        "flavorRef": "1",
        "availability_zone": "nova",
        "OS-DCF:diskConfig": "AUTO",
        "metadata": {
            "My Server Name": "Apache1"
        },
        "personality": [
            {
                "path": "/etc/banner.txt",
                "contents":
                    "ICAgICAgDQoiQSBjbG91ZCBkb2VzIG5vdCBrbm93IHdoeSBp "
                    "dCBtb3ZlcyBpbiBqdXN0IHN1Y2ggYSBkaXJlY3Rpb24gYW5k "
                    "IGF0IHN1Y2ggYSBzcGVlZC4uLkl0IGZlZWxzIGFuIGltcHVs "
                    "c2lvbi4uLnRoaXMgaXMgdGhlIHBsYWNlIHRvIGdvIG5vdy4g "
                    "QnV0IHRoZSBza3kga25vd3MgdGhlIHJlYXNvbnMgYW5kIHRo "
                    "ZSBwYXR0ZXJucyBiZWhpbmQgYWxsIGNsb3VkcywgYW5kIHlv "
                    "dSB3aWxsIGtub3csIHRvbywgd2hlbiB5b3UgbGlmdCB5b3Vy "
                    "c2VsZiBoaWdoIGVub3VnaCB0byBzZWUgYmV5b25kIGhvcml6 "
                    "b25zLiINCg0KLVJpY2hhcmQgQmFjaA=="
            }
        ],
        "security_groups": [
            {
                "name": "default"
            }
        ],
        "user_data":
            "IyEvYmluL2Jhc2gKL2Jpbi9zdQplY2hvICJJIGFtIGluIHlvdSEiCg=="
    },
    "OS-SCH-HNT:scheduler_hints": {
        "same_host": "48e6a9f6-30af-47e0-bc04-acaed113bb4e"
    }
}

MOCK_POST_SERVER_RESPONSE = {
    "server": {
        "OS-DCF:diskConfig": "AUTO",
        "adminPass": "6NpUwoz2QDRN",
        "id": "f5dc173b-6804-445a-a6d8-c705dad5b5eb",
        "links": [
            {
                "href": "http://openstack.example.com/v2/"
                        "6f70656e737461636b20342065766572/servers/"
                        "f5dc173b-6804-445a-a6d8-c705dad5b5eb",
                "rel": "self"
            },
            {
                "href": "http://openstack.example.com/"
                        "6f70656e737461636b20342065766572/servers/"
                        "f5dc173b-6804-445a-a6d8-c705dad5b5eb",
                "rel": "bookmark"
            }
        ],
        "security_groups": [
            {
                "name": "default"
            }
        ]
    }
}

MOCK_PATCH_IMAGE_REQUEST = [
    {
        "op": "replace",
        "path": "/name",
        "value": "Fedora 17"
    },
    {
        "op": "replace",
        "path": "/tags",
        "value": [
            "fedora",
            "beefy"
        ]
    }
]

MOCK_PATCH_IMAGE_RESPONSE = {
    "checksum": "710544e7f0c828b42f51207342622d33",
    "container_format": "ovf",
    "created_at": "2016-06-29T16:13:07Z",
    "disk_format": "vhd",
    "file": "/v2/images/2b61ed2b-f800-4da0-99ff-396b742b8646/file",
    "id": "2b61ed2b-f800-4da0-99ff-396b742b8646",
    "min_disk": 20,
    "min_ram": 512,
    "name": "Fedora 17",
    "owner": "02a7fb2dd4ef434c8a628c511dcbbeb6",
    "protected": "false",
    "schema": "/v2/schemas/image",
    "self": "/v2/images/2b61ed2b-f800-4da0-99ff-396b742b8646",
    "size": 21909,
    "status": "active",
    "tags": [
        "beefy",
        "fedora"
    ],
    "updated_at": "2016-07-25T14:48:18Z",
    "virtual_size": "",
    "visibility": "private"
}


class MockResponse(object):
    status_code = 200
    content = ''

    def json(self):
        pass


class TestServiceProxy(unittest.TestCase):
    def setUp(self):
        self.client = Client()

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_token_cache')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_get_token(self, mock_get_vim_info, mock_get_token_cache,
                       mock_get_session):
        mock_session_specs = ["head"]
        mock_session = mock.Mock(name='mock_session',
                                 spec=mock_session_specs)
        mock_get_servers_response_obj = mock.Mock(spec=MockResponse)
        mock_get_servers_response_obj.status_code = 200
        mock_get_servers_response_obj.content = MOCK_GET_SERVERS_RESPONSE
        mock_get_servers_response_obj.json.return_value = MOCK_GET_SERVERS_RESPONSE
        mock_session.head.return_value = mock_get_servers_response_obj

        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO
        mock_get_session.return_value = mock_session
        mock_get_token_cache.return_value = (
            json.dumps(mock_info.MOCK_AUTH_STATE),
            json.dumps(mock_info.MOCK_INTERNAL_METADATA_CATALOG))
        response = self.client.head(
            "/api/%s/v0/windriver-hudson-dc_RegionOne/compute/v2.1"
            "/fcca3cc49d5e42caae15459e27103efc/"
            "servers" % test_base.MULTIVIM_VERSION,
            {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)
        self.assertEquals(status.HTTP_200_OK, response.status_code)

    def test_unauthorized_access(self):
        response = self.client.get(
            "/api/%s/v0/windriver-hudson-dc_RegionOne/compute/v2.1/"
            "fcca3cc49d5e42caae15459e27103efc/"
            "servers" % test_base.MULTIVIM_VERSION)
        self.assertEquals(status.HTTP_403_FORBIDDEN,
                          response.status_code)

    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_expired_auth_token(self, mock_get_vim_info):
        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        response = self.client.get(
            "/api/%s/v0/windriver-hudson-dc_RegionOne/compute/v2.1/"
            "fcca3cc49d5e42caae15459e27103efc/"
            "servers" % test_base.MULTIVIM_VERSION,
            {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)
        self.assertEquals(status.HTTP_403_FORBIDDEN,
                          response.status_code)

    @mock.patch.object(VimDriverUtils, 'get_token_cache')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_request_without_servicetype(self, mock_get_vim_info,
                                         mock_get_token_cache):
        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO
        mock_get_token_cache.return_value = (
            json.dumps(mock_info.MOCK_AUTH_STATE), {})
        servicetype = "compute"
        url = (
            "/api/%s/v0/windriver-hudson-dc_RegionOne/%s/v2.1/"
            "fcca3cc49d5e42caae15459e27103efc/"
            "servers" % (test_base.MULTIVIM_VERSION, servicetype))
        response = self.client.get(
            url, {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)
        self.assertEquals(status.HTTP_500_INTERNAL_SERVER_ERROR,
                          response.status_code)

        metadata_catalog = copy.deepcopy(
            mock_info.MOCK_INTERNAL_METADATA_CATALOG)
        metadata_catalog[servicetype] = None
        mock_get_token_cache.return_value = (
            json.dumps(mock_info.MOCK_AUTH_STATE),
            json.dumps(metadata_catalog))

        response = self.client.get(
            url, {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)
        self.assertEquals(status.HTTP_500_INTERNAL_SERVER_ERROR,
                          response.status_code)

        metadata_catalog = copy.deepcopy(
            mock_info.MOCK_INTERNAL_METADATA_CATALOG)
        metadata_catalog[servicetype]['prefix'] = None
        metadata_catalog[servicetype]['proxy_prefix'] = None
        mock_get_token_cache.return_value = (
            json.dumps(mock_info.MOCK_AUTH_STATE),
            json.dumps(metadata_catalog))

        response = self.client.get(
            url, {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)
        self.assertEquals(status.HTTP_500_INTERNAL_SERVER_ERROR,
                          response.status_code)

    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_auth_state')
    @mock.patch.object(VimDriverUtils, 'update_token_cache')
    @mock.patch.object(VimDriverUtils, 'get_token_cache')
    def test_crud_resources(self, mock_get_token_cache,
                            mock_update_token_cache,
                            mock_get_auth_state, mock_get_session,
                            mock_get_vim_info):
        '''
        Test service proxy API: GET

        :param mock_get_token_cache:
        :param mock_update_token_cache:
        :param mock_get_auth_state:
        :param mock_get_session:
        :param mock_get_vim_info:
        :return:
        '''

        # mock VimDriverUtils APIs
        mock_session_specs = ["get", "post", "put", "patch", "delete"]

        mock_get_servers_response_obj = mock.Mock(spec=MockResponse)
        mock_get_servers_response_obj.status_code = 200
        mock_get_servers_response_obj.content = MOCK_GET_SERVERS_RESPONSE
        mock_get_servers_response_obj.json.return_value = MOCK_GET_SERVERS_RESPONSE

        mock_post_server_response_obj = mock.Mock(spec=MockResponse)
        mock_post_server_response_obj.status_code = 202
        mock_post_server_response_obj.content = MOCK_POST_SERVER_RESPONSE
        mock_post_server_response_obj.json.return_value = MOCK_POST_SERVER_RESPONSE

        mock_patch_server_response_obj = mock.Mock(spec=MockResponse)
        mock_patch_server_response_obj.status_code = 202
        mock_patch_server_response_obj.content = MOCK_PATCH_IMAGE_REQUEST
        mock_patch_server_response_obj.json.return_value = MOCK_PATCH_IMAGE_REQUEST

        mock_delete_server_response_obj = mock.Mock(spec=MockResponse)
        mock_delete_server_response_obj.status_code = 204

        mock_session = mock.Mock(name='mock_session',
                                 spec=mock_session_specs)
        mock_session.get.return_value = mock_get_servers_response_obj
        mock_session.post.return_value = mock_post_server_response_obj
        mock_session.patch.return_value = mock_patch_server_response_obj
        mock_session.delete.return_value = mock_delete_server_response_obj

        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO
        mock_get_session.return_value = mock_session
        mock_get_auth_state.return_value = json.dumps(
            mock_info.MOCK_AUTH_STATE)
        mock_update_token_cache.return_value = mock_info.MOCK_TOKEN_ID
        mock_get_token_cache.return_value = (
            json.dumps(mock_info.MOCK_AUTH_STATE),
            json.dumps(mock_info.MOCK_INTERNAL_METADATA_CATALOG))

        # Create resource
        response = self.client.post(
            "/api/%s/v0/windriver-hudson-dc_RegionOne/compute/v2.1/"
            "fcca3cc49d5e42caae15459e27103efc/"
            "servers" % test_base.MULTIVIM_VERSION,
            MOCK_POST_SERVER_REQUEST,
            HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        self.assertEquals(status.HTTP_202_ACCEPTED,
                          response.status_code)
        context = response.json()
        self.assertEquals(mock_info.MOCK_TOKEN_ID,
                          response['X-Subject-Token'])
        self.assertIsNotNone(context['server'])

        # Retrieve resource
        response = self.client.get(
            "/api/%s/v0/windriver-hudson-dc_RegionOne/compute/v2.1/"
            "fcca3cc49d5e42caae15459e27103efc/"
            "servers" % test_base.MULTIVIM_VERSION,
            {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        context = response.json()

        self.assertEquals(mock_info.MOCK_TOKEN_ID,
                          response['X-Subject-Token'])
        self.assertIsNotNone(context['servers'])

        # Update resource
        response = self.client.get(
            "/api/%s/v0/windriver-hudson-dc_RegionOne/compute/v2.1/"
            "fcca3cc49d5e42caae15459e27103efc/"
            "servers" % test_base.MULTIVIM_VERSION,
            {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        context = response.json()

        self.assertEquals(mock_info.MOCK_TOKEN_ID,
                          response['X-Subject-Token'])
        self.assertIsNotNone(context['servers'])

        # simulate client to make the request
        response = self.client.delete(
            "/api/%s/v0/windriver-hudson-dc_RegionOne/compute/v2.1/"
            "fcca3cc49d5e42caae15459e27103efc/servers/"
            "324dfb7d-f4a9-419a-9a19-237df04b443b" % test_base.MULTIVIM_VERSION,
            HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        self.assertEquals(status.HTTP_204_NO_CONTENT,
                          response.status_code)
        self.assertEquals(mock_info.MOCK_TOKEN_ID,
                          response['X-Subject-Token'])
