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

from newton.requests.views.util import VimDriverUtils
from newton.requests.tests import mock_info


MOCK_GET_NETWORKS_RESPONSE = {
    "networks": [
        {"name": "network_1"},
        {"name": "network_2"}
    ]
}

MOCK_GET_NETWORK_RESPONSE = {
    "network": {
        "network_id": "f5dc173b-6804-445a-a6d8-c705dad5b5eb",
        "name": "network_3"
    }
}

MOCK_POST_NETWORK_REQUEST = {
    "name": "network_3"
}

MOCK_POST_NETWORK_REQUEST_EXISTING = {
    "name": "network_1"
}

MOCK_POST_NETWORK_RESPONSE = {
    "network": {
        "network_id": "f5dc173b-6804-445a-a6d8-c705dad5b5eb"
    }
}


class MockResponse(object):
    status_code = 200
    content = ''

    def json(self):
        pass


class TestNetwork(unittest.TestCase):
   def setUp(self):
      self.client = Client()

   def tearDown(self):
      pass

   @mock.patch.object(VimDriverUtils, 'get_session')
   @mock.patch.object(VimDriverUtils, 'get_vim_info')
   def test_get_networks(self, mock_get_vim_info, mock_get_session):

       mock_session_specs = ["get"]
       mock_session = mock.Mock(name='mock_session', spec=mock_session_specs)
       mock_get_networks_response_obj = mock.Mock(spec=MockResponse)
       mock_get_networks_response_obj.status_code = 200
       mock_get_networks_response_obj.content = MOCK_GET_NETWORKS_RESPONSE
       mock_get_networks_response_obj.json.return_value = MOCK_GET_NETWORKS_RESPONSE
       mock_session.get.return_value = mock_get_networks_response_obj

       mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO
       mock_get_session.return_value = mock_session

       response = self.client.get(
         "/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne/fcca3cc49d5e42caae15459e27103efc/networks",
          {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

       context = response.json()
       self.assertEquals(status.HTTP_200_OK, response.status_code)
       self.assertIsNotNone(context['networks'])
       self.assertEqual(MOCK_GET_NETWORKS_RESPONSE["networks"], context['networks'])

   @mock.patch.object(VimDriverUtils, 'get_session')
   @mock.patch.object(VimDriverUtils, 'get_vim_info')
   def test_get_network(self, mock_get_vim_info, mock_get_session):

       mock_session_specs = ["get"]
       mock_session = mock.Mock(name='mock_session', spec=mock_session_specs)
       mock_get_network_response_obj = mock.Mock(spec=MockResponse)
       mock_get_network_response_obj.status_code = 200
       mock_get_network_response_obj.content = MOCK_GET_NETWORK_RESPONSE
       mock_get_network_response_obj.json.return_value = MOCK_GET_NETWORK_RESPONSE
       mock_session.get.return_value = mock_get_network_response_obj

       mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO
       mock_get_session.return_value = mock_session

       response = self.client.get(
           "/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne/fcca3cc49d5e42caae15459e27103efc"
           "/networks/f5dc173b-6804-445a-a6d8-c705dad5b5eb",
           {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

       context = response.json()
       self.assertEquals(status.HTTP_200_OK, response.status_code)
       self.assertEquals(MOCK_GET_NETWORK_RESPONSE['network_id'], context['network_id'])

   @mock.patch.object(VimDriverUtils, 'get_session')
   @mock.patch.object(VimDriverUtils, 'get_vim_info')
   def test_get_network_not_found(self, mock_get_vim_info, mock_get_session):

       mock_session_specs = ["get"]
       mock_session = mock.Mock(name='mock_session', spec=mock_session_specs)
       mock_get_network_response_obj = mock.Mock(spec=MockResponse)
       mock_get_network_response_obj.status_code = 404
       mock_get_network_response_obj.context = {}
       mock_get_network_response_obj.json.return_value = {}
       mock_session.get.return_value = mock_get_network_response_obj

       mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO
       mock_get_session.return_value = mock_session

       response = self.client.get(
           "/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne/fcca3cc49d5e42caae15459e27103efc"
           "/networks/f5dc173b-6804-445a-a6d8-c705dad5b5eb",
           {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

       # TODO(sshank): 404 status is not possible.
       self.assertEquals(status.HTTP_500_INTERNAL_SERVER_ERROR, response.status_code)
       self.assertIn('error', response.data)

   @mock.patch.object(VimDriverUtils, 'get_session')
   @mock.patch.object(VimDriverUtils, 'get_vim_info')
   def test_post(self, mock_get_vim_info, mock_get_session):

       mock_session_specs = ["get", "post"]
       mock_session = mock.Mock(name='mock_session', spec=mock_session_specs)

       mock_get_networks_response_obj = mock.Mock(spec=MockResponse)
       mock_get_networks_response_obj.status_code = 200
       mock_get_networks_response_obj.content = MOCK_GET_NETWORKS_RESPONSE
       mock_get_networks_response_obj.json.return_value = MOCK_GET_NETWORKS_RESPONSE

       mock_post_network_response_obj = mock.Mock(spec=MockResponse)
       mock_post_network_response_obj.status_code = 202
       mock_post_network_response_obj.content = MOCK_POST_NETWORK_RESPONSE
       mock_post_network_response_obj.json.return_value = MOCK_POST_NETWORK_RESPONSE

       mock_session.get.return_value = mock_get_networks_response_obj
       mock_session.post.return_value = mock_post_network_response_obj

       mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO
       mock_get_session.return_value = mock_session

       response = self.client.post(
           "/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne/fcca3cc49d5e42caae15459e27103efc/networks",
           MOCK_POST_NETWORK_REQUEST, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

       context = response.json()
       self.assertEquals(status.HTTP_202_ACCEPTED, response.status_code)
       self.assertIsNotNone(context['network_id'])
       self.assertEqual(1, context['returnCode'])

   @mock.patch.object(VimDriverUtils, 'get_session')
   @mock.patch.object(VimDriverUtils, 'get_vim_info')
   def test_post_existing(self, mock_get_vim_info, mock_get_session):
       mock_session_specs = ["get", "post"]
       mock_session = mock.Mock(name='mock_session', spec=mock_session_specs)

       mock_get_networks_response_obj = mock.Mock(spec=MockResponse)
       mock_get_networks_response_obj.status_code = 200
       mock_get_networks_response_obj.content = MOCK_GET_NETWORKS_RESPONSE
       mock_get_networks_response_obj.json.return_value = MOCK_GET_NETWORKS_RESPONSE

       mock_post_network_response_obj = mock.Mock(spec=MockResponse)
       mock_post_network_response_obj.status_code = 202
       mock_post_network_response_obj.content = MOCK_POST_NETWORK_RESPONSE
       mock_post_network_response_obj.json.return_value = MOCK_POST_NETWORK_RESPONSE

       mock_session.get.return_value = mock_get_networks_response_obj
       mock_session.post.return_value = mock_post_network_response_obj

       mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO
       mock_get_session.return_value = mock_session

       response = self.client.post(
           "/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne/fcca3cc49d5e42caae15459e27103efc/networks",
           MOCK_POST_NETWORK_REQUEST_EXISTING, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

       context = response.json()
       self.assertEquals(status.HTTP_200_OK, response.status_code)
       self.assertIsNotNone(context['returnCode'])
       self.assertEqual(0, context['returnCode'])

   @mock.patch.object(VimDriverUtils, 'get_session')
   @mock.patch.object(VimDriverUtils, 'get_vim_info')
   def test_post_empty_body(self, mock_get_vim_info, mock_get_session):
       mock_session_specs = ["get", "post"]
       mock_session = mock.Mock(name='mock_session', spec=mock_session_specs)

       mock_get_networks_response_obj = mock.Mock(spec=MockResponse)
       mock_get_networks_response_obj.status_code = 200
       mock_get_networks_response_obj.content = MOCK_GET_NETWORKS_RESPONSE
       mock_get_networks_response_obj.json.return_value = MOCK_GET_NETWORKS_RESPONSE

       mock_post_network_response_obj = mock.Mock(spec=MockResponse)
       mock_post_network_response_obj.status_code = 202
       mock_post_network_response_obj.content = MOCK_POST_NETWORK_RESPONSE
       mock_post_network_response_obj.json.return_value = MOCK_POST_NETWORK_RESPONSE

       mock_session.get.return_value = mock_get_networks_response_obj
       mock_session.post.return_value = mock_post_network_response_obj

       mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO
       mock_get_session.return_value = mock_session

       response = self.client.post(
           "/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne/fcca3cc49d5e42caae15459e27103efc/networks",
           {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

       context = response.json()
       self.assertIn('error', context)
       self.assertEquals(status.HTTP_500_INTERNAL_SERVER_ERROR, response.status_code)

   @mock.patch.object(VimDriverUtils, 'get_session')
   @mock.patch.object(VimDriverUtils, 'get_vim_info')
   def test_delete(self, mock_get_vim_info, mock_get_session):

       mock_session_specs = ["delete"]
       mock_session = mock.Mock(name='mock_session', spec=mock_session_specs)

       mock_delete_network_response_obj = mock.Mock(spec=MockResponse)
       mock_delete_network_response_obj.status_code = 204

       mock_session.delete.return_value = mock_delete_network_response_obj

       mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO
       mock_get_session.return_value = mock_session

       response = self.client.delete(
           "/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne/fcca3cc49d5e42caae15459e27103efc"
           "/networks/f5dc173b-6804-445a-a6d8-c705dad5b5eb",
           HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

       self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
       self.assertIsNone(response.data)
