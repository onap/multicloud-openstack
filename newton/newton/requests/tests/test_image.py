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

from six.moves import urllib
from django.test import Client
from rest_framework import status

from newton.requests.tests import mock_info
from newton.requests.tests import test_base
from newton.requests.views.image import imageThread
from newton.requests.views.util import VimDriverUtils

from newton.requests.tests.test_base import AbstractTestResource


class TestImageNewton(unittest.TestCase, AbstractTestResource):

    def setUp(self):
        self.client = Client()

        self.openstack_version = "newton"
        self.resource_name = "images"

        self.MOCK_GET_RESOURCES_RESPONSE = {
            "images": [
                {"id": "uuid_1", "name": "image_1"},
                {"id": "uuid_2", "name": "image_2"}
            ]
        }

        self.MOCK_GET_RESOURCE_RESPONSE = {
            "image": {
                "id": "uuid_1",
                "name": "image_1"
            }
        }

        self.MOCK_POST_RESOURCE_REQUEST = {
            "id": "uuid_3",
            "name": "image_3",
            "imagePath": "test.com/image_3"
        }

        self.MOCK_POST_RESOURCE_REQUEST_EXISTING = {
            "id": "uuid_1",
            "name": "image_1",
            "imagePath": "test.com/image_1"
        }

        self.MOCK_POST_RESOURCE_RESPONSE = {
            "id": "uuid_3",
            "name": "image_3"
        }

        self.assert_keys = "images"
        self.assert_key = "image"

        self.HTTP_not_found = 404

    @mock.patch.object(imageThread, 'run')
    @mock.patch.object(urllib, 'request')
    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_post_image(self, mock_get_vim_info, mock_get_session, mock_request, mock_run):

        mock_get_session.side_effect = [
            test_base.get_mock_session(
                ["get"], {"get": {"content": self.MOCK_GET_RESOURCES_RESPONSE}}),
            test_base.get_mock_session(
                ["post"], {"post": {"content": self.MOCK_POST_RESOURCE_RESPONSE,
                                    "status_code": 201}}),
        ]

        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        mock_request.urlopen.return_value = "image"

        response = self.client.post(
            "/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne/fcca3cc49d5e42caae15459e27103efc/images",
            self.MOCK_POST_RESOURCE_REQUEST, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        context = response.json()
        self.assertEquals(status.HTTP_201_CREATED, response.status_code)
        self.assertIsNotNone(context['id'])
        self.assertEqual(1, context['returnCode'])

    # Overridden method from test base to not make it run for current test case.
    def test_post_resource(self):
        pass
