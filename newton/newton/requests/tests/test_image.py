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


MOCK_GET_IMAGES_RESPONSE = {
    "images": [
        {"id": "uuid_1", "name": "image_1"},
        {"id": "uuid_2", "name": "image_2"}
    ]
}

MOCK_GET_IMAGE_RESPONSE = {
    "image": {
        "id": "uuid_1",
        "name": "image_1"
    }
}

MOCK_POST_IMAGE_REQUEST = {
    "id": "uuid_3",
    "name": "image_3",
    "imagePath": "test.com/image_3"
}

MOCK_POST_IMAGE_REQUEST_EXISTING = {
    "id": "uuid_1",
    "name": "image_1",
    "imagePath": "test.com/image_1"
}

MOCK_POST_IMAGE_RESPONSE = {
    "id": "uuid_3",
    "name": "image_3"
}


class MockResponse(object):
    status_code = 200
    content = ''

    def json(self):
        pass


class TestImage(unittest.TestCase):
    def setUp(self):
        self.client = Client()
    def tearDown(self):
        pass

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_get_images(self, mock_get_vim_info, mock_get_session):

        mock_get_session.side_effect = [
            test_base.get_mock_session(
                ["get"], {"get": {"content": MOCK_GET_IMAGES_RESPONSE}}),
        ]

        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        response = self.client.get(
            "/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne/fcca3cc49d5e42caae15459e27103efc/images",
            {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        context = response.json()
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertIsNotNone(context['images'])
        self.assertEqual(MOCK_GET_IMAGES_RESPONSE["images"], context["images"])

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_get_image(self, mock_get_vim_info, mock_get_session):

        mock_get_session.side_effect = [
            test_base.get_mock_session(
                ["get"], {"get": {"content": MOCK_GET_IMAGE_RESPONSE}}),
        ]

        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        response = self.client.get(
            "/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne/fcca3cc49d5e42caae15459e27103efc"
            "/images/uuid_1",
            {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)
        context = response.json()

        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertEqual(MOCK_GET_IMAGE_RESPONSE["image"], context["image"])

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_get_image_not_found(self, mock_get_vim_info, mock_get_session):

        mock_get_session.side_effect = [
            test_base.get_mock_session(
                ["get"], {"get": {"content": {},
                                  "status_code": 404}})
        ]

        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        response = self.client.get(
            "/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne/fcca3cc49d5e42caae15459e27103efc"
            "/images/uuid_3",
            {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)
        context = response.json()

        self.assertEquals(status.HTTP_404_NOT_FOUND, response.status_code)
        self.assertIsNone(context.get("image"))

    @mock.patch.object(imageThread, 'run')
    @mock.patch.object(urllib, 'request')
    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_post_image(self, mock_get_vim_info, mock_get_session, mock_request, mock_run):

        mock_get_session.side_effect = [
            test_base.get_mock_session(
                ["get"], {"get": {"content": MOCK_GET_IMAGES_RESPONSE}}),
            test_base.get_mock_session(
                ["post"], {"post": {"content": MOCK_POST_IMAGE_RESPONSE,
                                    "status_code": 201}}),
        ]

        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        mock_request.urlopen.return_value = "image"

        response = self.client.post(
            "/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne/fcca3cc49d5e42caae15459e27103efc/images",
            MOCK_POST_IMAGE_REQUEST, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        context = response.json()
        self.assertEquals(status.HTTP_201_CREATED, response.status_code)
        self.assertIsNotNone(context['id'])
        self.assertEqual(1, context['returnCode'])

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_post_image_existing(self, mock_get_vim_info, mock_get_session):

        mock_get_session.side_effect = [
            test_base.get_mock_session(
                ["get"], {"get": {"content": MOCK_GET_IMAGES_RESPONSE}}),
            test_base.get_mock_session(
                ["post"], {"post": {"content": MOCK_POST_IMAGE_RESPONSE,
                                    "status_code": 201}}),
        ]

        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        response = self.client.post(
            "/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne/fcca3cc49d5e42caae15459e27103efc/images",
            MOCK_POST_IMAGE_REQUEST_EXISTING, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        context = response.json()
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertIsNotNone(context['returnCode'])
        self.assertEqual(0, context['returnCode'])

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_post_image_empty(self, mock_get_vim_info, mock_get_session):

        mock_get_session.side_effect = [
            test_base.get_mock_session(
                ["get"], {"get": {"content": MOCK_GET_IMAGES_RESPONSE}}),
            test_base.get_mock_session(
                ["post"], {"post": {"content": MOCK_POST_IMAGE_RESPONSE,
                                    "status_code": 201}}),
        ]

        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        response = self.client.post(
            "/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne/fcca3cc49d5e42caae15459e27103efc/images",
            {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        context = response.json()
        self.assertIn('error', context)
        self.assertEquals(status.HTTP_500_INTERNAL_SERVER_ERROR, response.status_code)

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_delete_image(self, mock_get_vim_info, mock_get_session):

        mock_get_session.side_effect = [
            test_base.get_mock_session(
                ["delete"], {"delete": {"content": {},
                                        "status_code": 204}})
        ]

        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        response = self.client.delete(
            "/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne/fcca3cc49d5e42caae15459e27103efc"
            "/images/uuid_1", HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertIsNone(response.data)
