# Copyright (c) 2018 Intel Corporation, Inc.
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

from newton.requests.tests import mock_info
from newton.requests.tests import test_base
from newton.requests.tests.test_base import AbstractTestResource
from newton.requests.views.util import VimDriverUtils
from ocata.requests.views.trait import Traits


class TestTraitsOcata(unittest.TestCase, AbstractTestResource):

    def setUp(self):
        AbstractTestResource.__init__(self)

        self.url += "traits"

        self.MOCK_GET_RESOURCES_RESPONSE = {
            "traits": [
                "trait_1",
                "trait_2",
                "trait_3"
            ]
        }

        self.HTTP_not_found = status.HTTP_404_NOT_FOUND

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_get_traits(self, mock_get_vim_info, mock_get_session):
        mock_get_session.side_effect = [
            test_base.get_mock_session(
            ["get"], {"get": {
                    "content": self.MOCK_GET_RESOURCES_RESPONSE}}),
        ]

        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        response = self.client.get(
            ("/api/%s/v0/windriver-hudson-dc_RegionOne"
             "/fcca3cc49d5e42caae15459e27103efc/"
             "traits" % test_base.MULTIVIM_VERSION),
            {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)
        context = response.json()

        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertIsNotNone(context['traits'])
        self.assertEqual(self.MOCK_GET_RESOURCES_RESPONSE['traits'],
                         context['traits'])

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_get_trait_not_found(self, mock_get_vim_info, mock_get_session):
        mock_get_session.side_effect = [
           test_base.get_mock_session(
               ["get"],
               {"get": {"status_code": status.HTTP_404_NOT_FOUND}}),
        ]

        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        response = self.client.get(
            ("/api/%s/v0/windriver-hudson-dc_RegionOne"
             "/fcca3cc49d5e42caae15459e27103efc/traits/"
             "trait_4" % test_base.MULTIVIM_VERSION),
            {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        # TODO(ntpttr): 404 status is not possible, as the handler on
        # the multicloud side will convert it to 500.
        self.assertEquals(status.HTTP_500_INTERNAL_SERVER_ERROR,
                         response.status_code)
        self.assertIn('error', response.data)

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_create_trait(self, mock_get_vim_info, mock_get_session):
        mock_get_session.side_effect = [
            test_base.get_mock_session(
                ["get", "put"], {
                    "get": {
                        "status_code": status.HTTP_404_NOT_FOUND},
                    "put": {
                        "content": self.MOCK_PUT_RESOURCE_RESPONSE,
                        "status_code": status.HTTP_201_CREATED,
                    }
                }
            ),
        ]
        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        response = self.client.put(
            ("/api/%s/v0/windriver-hudson-dc_RegionOne"
             "/fcca3cc49d5e42caae15459e27103efc/"
             "traits/CUSTOM_trait_4" % test_base.MULTIVIM_VERSION),
            self.MOCK_PUT_RESOURCE_REQUEST,
            HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)
        context = response.json()

        self.assertEquals(status.HTTP_201_CREATED,
                          response.status_code)
        self.assertEqual(1, context['returnCode'])

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_create_existing_trait(self, mock_get_vim_info, mock_get_session):
       mock_get_session.side_effect = [
           test_base.get_mock_session(
               ["get", "put"], {
                   "get": {
                       "content":  self.MOCK_GET_RESOURCES_RESPONSE},
                   "put": {
                       "content": self.MOCK_PUT_RESOURCE_RESPONSE,
                       "status_code": status.HTTP_202_ACCEPTED,
                   }
               }),
       ]
       mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

       response = self.client.put(
           ("/api/%s/v0/windriver-hudson-dc_RegionOne/"
            "fcca3cc49d5e42caae15459e27103efc/"
            "traits/CUSTOM_trait_4" % test_base.MULTIVIM_VERSION),
           self.MOCK_PUT_RESOURCE_REQUEST,
           HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

       context = response.json()
       self.assertEquals(status.HTTP_200_OK, response.status_code)
       self.assertIsNotNone(context['returnCode'])
       self.assertEqual(0, context['returnCode'])

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_delete_trait(self, mock_get_vim_info, mock_get_session):
        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO
        mock_get_session.side_effect = [
            test_base.get_mock_session(
                ["delete"],
                {
                    "delete": {
                        "status_code": status.HTTP_204_NO_CONTENT }
                }),
        ]

        response = self.client.delete(
            ("/api/%s/v0/windriver-hudson-dc_RegionOne/"
             "fcca3cc49d5e42caae15459e27103efc/traits/"
             "trait_1" % test_base.MULTIVIM_VERSION),
            HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        self.assertEqual(status.HTTP_204_NO_CONTENT,
                        response.status_code)
        self.assertIsNone(response.data)



    # Overridden methods from test base to not make it run for current test case.
    def test_get_resources_list(self):
        pass

    def test_get_resource_info(self):
        pass

    def test_get_resource_not_found(self):
        pass

    def test_post_resource(self):
        pass

    def test_post_resource_existing(self):
        pass

    def test_post_resource_empty(self):
        pass

    def test_delete_resource(self):
        pass

