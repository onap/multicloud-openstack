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

from newton_base.tests import mock_info
from newton_base.tests import test_base
from newton_base.tests.test_base import AbstractTestResource
from newton_base.util import VimDriverUtils


class TestLimitNewton(unittest.TestCase, AbstractTestResource):
    def setUp(self):
        self.client = Client()

        self.openstack_version = "newton"
        self.region = "windriver-hudson-dc_RegionOne"
        self.resource_name = "limits"

        self.MOCK_GET_LIMITS_RESPONSE = {
            "limits": {
                "absolute": {
                    "id": "uuid_1", "name": "limit_1"
                }
            }
        }

        self.MOCK_GET_QUOTAS_RESPONSE = {
            "quota": {"limit": "1"}
        }

    @staticmethod
    def _get_mock_response(return_value=None):
        mock_response = mock.Mock(spec=test_base.MockResponse)
        mock_response.status_code = status.HTTP_200_OK
        mock_response.json.return_value = return_value
        return mock_response

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_get_limits_list(
            self, mock_get_vim_info, mock_get_session):
        mock_get_session.return_value = test_base.get_mock_session(
            ["get"], {
                "side_effect": [
                    self._get_mock_response(
                        self.MOCK_GET_LIMITS_RESPONSE),
                    self._get_mock_response(
                        self.MOCK_GET_QUOTAS_RESPONSE),
                    self._get_mock_response(
                        self.MOCK_GET_LIMITS_RESPONSE)
                ]
            })

        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        response = self.client.get(
            "/api/%s/v0/windriver-hudson-dc_RegionOne/"
            "fcca3cc49d5e42caae15459e27103efc/"
            "limits" % test_base.MULTIVIM_VERSION,
            {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        context = response.json()
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertIsNotNone(context)
        self.assertIn(
            self.MOCK_GET_LIMITS_RESPONSE["limits"]["absolute"]['id'],
            context['id'])

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_get_limits_list_failure(
            self, mock_get_vim_info, mock_get_session):
        mock_get_session.return_value = test_base.get_mock_session(
            ["get"], {
                "side_effect": [
                    self._get_mock_response(
                        self.MOCK_GET_LIMITS_RESPONSE),
                    self._get_mock_response({}),
                    self._get_mock_response(
                        self.MOCK_GET_LIMITS_RESPONSE)
                ]
            })

        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        response = self.client.get(
            "/api/%s/v0/windriver-hudson-dc_RegionOne/"
            "fcca3cc49d5e42caae15459e27103efc/"
            "limits" % test_base.MULTIVIM_VERSION,
            {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        context = response.json()
        self.assertIn('error', context)
        self.assertEquals(status.HTTP_500_INTERNAL_SERVER_ERROR,
                          response.status_code)

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
