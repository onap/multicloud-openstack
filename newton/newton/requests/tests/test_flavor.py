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

from newton.requests.tests import mock_info
from newton.requests.tests import test_base
from newton.requests.tests.test_base import AbstractTestResource
from newton.requests.views.flavor import Flavors
from newton.requests.views.util import VimDriverUtils


class TestFlavorsNewton(unittest.TestCase, AbstractTestResource):

    def setUp(self):
        AbstractTestResource.__init__(self)

        self.url += "flavors"

        self.MOCK_GET_RESOURCES_RESPONSE = {
            "flavors": [
                {"id": "uuid_1", "name": "flavor_1"},
                {"id": "uuid_2", "name": "flavor_2"}
            ]
        }

        self.MOCK_GET_RESOURCE_RESPONSE = {
            "flavor": {
                "id": "uuid_1",
                "name": "flavor_1"
            }
        }

        self.MOCK_GET_RESOURCE_RESPONSE_NOT_FOUND = {}

        self.MOCK_POST_RESOURCE_REQUEST = {
            "id": "uuid_3",
            "name": "flavor_3"
        }

        self.MOCK_POST_RESOURCE_REQUEST_EXISTING = {
            "id": "uuid_1",
            "name": "flavor_1"
        }

        self.MOCK_POST_RESOURCE_RESPONSE = {
             "flavor": {
            "id": "uuid_3",
            "name": "flavor_3"
            }
        }

        self.MOCK_GET_EXTRA_SPECS = {
            "extra_specs": {
                "key": "test"
            }
        }

        self.assert_keys = "flavors"
        self.assert_key = "flavor"

        self.HTTP_not_found = status.HTTP_404_NOT_FOUND

    @mock.patch.object(Flavors, '_get_flavor_extra_specs')
    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_get_flavors(self, mock_get_vim_info, mock_get_session,
                          mock_get_flavor_extra_specs):
        mock_get_session.side_effect = [
            test_base.get_mock_session(
            ["get"], {"get": {"content": self.MOCK_GET_RESOURCES_RESPONSE}}),
        ]

        mock_extra_specs = mock.Mock(spec=test_base.MockResponse)
        mock_extra_specs.json.return_value = {"extra_specs": {}}

        mock_get_flavor_extra_specs.return_value = mock_extra_specs
        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        response = self.client.get(
            ("/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne"
             "/fcca3cc49d5e42caae15459e27103efc/flavors"),
            {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)
        context = response.json()

        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertIsNotNone(context['flavors'])
        self.assertEqual(self.MOCK_GET_RESOURCES_RESPONSE["flavors"],
                         context['flavors'])

    @mock.patch.object(Flavors, '_get_flavor_extra_specs')
    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_get_flavor(self, mock_get_vim_info, mock_get_session,
                        mock_get_flavor_extra_specs):
        mock_get_session.side_effect = [
            test_base.get_mock_session(
                ["get"],
                {"get": {"content": self.MOCK_GET_RESOURCE_RESPONSE}}),
        ]

        mock_extra_specs = mock.Mock(spec=test_base.MockResponse)
        mock_extra_specs.json.return_value = {"extra_specs": {}}

        mock_get_flavor_extra_specs.return_value = mock_extra_specs
        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        response = self.client.get(
            ("/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne"
             "/fcca3cc49d5e42caae15459e27103efc/flavors/uuid_1"),
            {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)
        context = response.json()

        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertEqual(self.MOCK_GET_RESOURCE_RESPONSE["id"], context["id"])

    @mock.patch.object(Flavors, '_get_flavor_extra_specs')
    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_get_flavor_not_found(
            self, mock_get_vim_info, mock_get_session,
            mock_get_flavor_extra_specs):
        mock_get_session.side_effect = [
           test_base.get_mock_session(
               ["get"],
               {"get": {"status_code":status.HTTP_404_NOT_FOUND}}),
        ]

        mock_extra_specs = mock.Mock(spec=test_base.MockResponse)
        mock_extra_specs.json.return_value = {"extra_specs": {}}

        mock_get_flavor_extra_specs.return_value = mock_extra_specs
        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        response = self.client.get(
            ("/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne"
             "/fcca3cc49d5e42caae15459e27103efc/flavors/uuid_1"),
            {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        # TODO(sshank): 404 status is not possible.
        self.assertEquals(status.HTTP_500_INTERNAL_SERVER_ERROR,
                         response.status_code)
        self.assertIn('error', response.data)

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_create_flavor(self, mock_get_vim_info, mock_get_session):
        mock_get_session.side_effect = [
            test_base.get_mock_session(
                ["get", "post"], {
                    "get": {"content": self.MOCK_GET_RESOURCES_RESPONSE},
                    "post": {
                        "content": self.MOCK_POST_RESOURCE_RESPONSE,
                        "status_code": status.HTTP_202_ACCEPTED,
                    }
                }
            ),
        ]
        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        response = self.client.post(
            ("/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne"
             "/fcca3cc49d5e42caae15459e27103efc/flavors"),
            self.MOCK_POST_RESOURCE_REQUEST,
            HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)
        context = response.json()

        self.assertEquals(status.HTTP_202_ACCEPTED,
                          response.status_code)
        self.assertIsNotNone(context['id'])
        self.assertEqual(1, context['returnCode'])

    @mock.patch.object(Flavors, '_get_flavor_extra_specs')
    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_create_existing_flavor(
           self, mock_get_vim_info, mock_get_session,
           mock_get_flavor_extra_specs):
       mock_get_session.side_effect = [
           test_base.get_mock_session(
               ["get", "post"], {
                   "get": {"content":  self.MOCK_GET_RESOURCES_RESPONSE},
                   "post": {
                       "content": self.MOCK_POST_RESOURCE_RESPONSE,
                       "status_code": status.HTTP_202_ACCEPTED,
                   }
               }),
       ]
       mock_extra_specs = mock.Mock(spec=test_base.MockResponse)
       mock_extra_specs.json.return_value = {"extra_specs": {}}

       mock_get_flavor_extra_specs.return_value = mock_extra_specs
       mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

       response = self.client.post(
           ("/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne/"
            "fcca3cc49d5e42caae15459e27103efc/flavors"),
           self.MOCK_POST_RESOURCE_REQUEST_EXISTING,
           HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

       context = response.json()
       self.assertEquals(status.HTTP_200_OK, response.status_code)
       self.assertIsNotNone(context['returnCode'])
       self.assertEqual(0, context['returnCode'])

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_delete_flavor(self, mock_get_vim_info, mock_get_session):
        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO
        mock_get_session.side_effect = [
            test_base.get_mock_session(
                ["get", "delete"],
                {
                    "get": { "content": self.MOCK_GET_EXTRA_SPECS },
                    "delete": {"status_code": status.HTTP_204_NO_CONTENT }
                }),
        ]

        response = self.client.delete(
            ("/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne/"
             "fcca3cc49d5e42caae15459e27103efc/flavors/uuid_1"),
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

    def test_delete_resource(self):
        pass
