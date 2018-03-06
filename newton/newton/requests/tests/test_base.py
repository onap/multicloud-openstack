# Copyright (c) 2017-2018 Wind River Systems, Inc.
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
import unittest

from abc import ABCMeta
from django.conf import settings
from django.test import Client

from newton.requests.tests import mock_info
from newton.requests.views.util import VimDriverUtils

MULTIVIM_VERSION = settings.MULTIVIM_VERSION


class MockResponse(object):
    status_code = status.HTTP_200_OK
    content = ''

    def json(self):
        pass


def get_mock_session(http_actions, response_dict={}):
    mock_session = mock.Mock(
        name='mock_session',spec=http_actions)
    for action in http_actions:
        side_effect = response_dict.get("side_effect")
        if side_effect and isinstance(side_effect, list):
            mock_session.__getattr__(action).__setattr__(
                "side_effect", side_effect)
        else:
            mock_response_obj = mock.Mock(spec=MockResponse)
            mock_response_obj.content = response_dict.get(
                action).get("content")
            mock_response_obj.json.return_value = response_dict.get(
                action).get("content")
            mock_response_obj.status_code = response_dict.get(
                action).get("status_code", status.HTTP_200_OK)
            mock_session.__getattr__(action).__setattr__(
                "return_value", mock_response_obj)

    return mock_session


class TestRequest(unittest.TestCase):

    def setUp(self):
        self.client = Client()


class AbstractTestResource(object):
    __metaclass__ = ABCMeta

    def __init__(self):

        self.client = Client()

        self.region = "windriver-hudson-dc_RegionOne"
        self.url = ("/api/%s/v0/%s/"
                   "fcca3cc49d5e42caae15459e27103efc/" % (
            MULTIVIM_VERSION, self.region))

        self.MOCK_GET_RESOURCES_RESPONSE = {}
        self.MOCK_GET_RESOURCE_RESPONSE = {}
        self.MOCK_GET_RESOURCE_RESPONSE_NOT_FOUND = {}

        self.MOCK_POST_RESOURCE_REQUEST = {}
        self.MOCK_POST_RESOURCE_REQUEST_EXISTING = {}

        self.MOCK_POST_RESOURCE_RESPONSE = {}

        self.assert_keys = ""
        self.assert_key = ""

        self.HTTP_not_found = status.HTTP_404_NOT_FOUND

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_get_resources_list(
            self, mock_get_vim_info, mock_get_session):
        mock_get_session.side_effect = [
            get_mock_session(
                ["get"], {"get": {
                    "content": self.MOCK_GET_RESOURCES_RESPONSE}}),
        ]

        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        response = self.client.get(
            self.url, {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        context = response.json()
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertIsNotNone(context[self.assert_keys])
        self.assertEqual(
            self.MOCK_GET_RESOURCES_RESPONSE[self.assert_keys],
            context[self.assert_keys])

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_get_resource_info(
            self, mock_get_vim_info, mock_get_session):
        mock_get_session.side_effect = [
            get_mock_session(
                ["get"], {"get": {
                    "content": self.MOCK_GET_RESOURCE_RESPONSE}}),
        ]

        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        response = self.client.get(
            self.url + "/uuid_1", {},
            HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        context = response.json()
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertEquals(
            self.MOCK_GET_RESOURCE_RESPONSE[self.assert_key],
            context[self.assert_key])

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_get_resource_not_found(
            self, mock_get_vim_info, mock_get_session):
        mock_get_session.side_effect = [
            get_mock_session(
                ["get"], {
                    "get": {
                        "content": self.MOCK_GET_RESOURCE_RESPONSE_NOT_FOUND,
                        "status_code": 404
                    }
                }
            ),
        ]

        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        response = self.client.get(
            self.url + "/uuid_3", {},
            HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        self.assertEquals(self.HTTP_not_found, response.status_code)

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_post_resource(self, mock_get_vim_info, mock_get_session):
        mock_get_session.side_effect = [
            get_mock_session(
                ["get"], {"get": {
                    "content": self.MOCK_GET_RESOURCES_RESPONSE}}),
            get_mock_session(
                ["post"], {"post": {
                    "content": self.MOCK_POST_RESOURCE_RESPONSE,
                    "status_code": 202}}),
        ]

        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        response = self.client.post(
            self.url, self.MOCK_POST_RESOURCE_REQUEST,
            HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        context = response.json()
        self.assertEquals(status.HTTP_202_ACCEPTED,
                          response.status_code)
        self.assertIsNotNone(context['id'])
        self.assertEqual(1, context['returnCode'])

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_post_resource_existing(
            self, mock_get_vim_info, mock_get_session):
        mock_get_session.side_effect = [
            get_mock_session(
                ["get"], {"get": {
                    "content": self.MOCK_GET_RESOURCES_RESPONSE}}),
            get_mock_session(
                ["post"], {"post": {
                    "content": self.MOCK_POST_RESOURCE_RESPONSE,
                    "status_code": 201}}),
        ]

        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        response = self.client.post(
            self.url, self.MOCK_POST_RESOURCE_REQUEST_EXISTING,
            HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        context = response.json()
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertIsNotNone(context['returnCode'])
        self.assertEqual(0, context['returnCode'])

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_post_resource_empty(
            self, mock_get_vim_info, mock_get_session):
        mock_get_session.side_effect = [
            get_mock_session(
                ["get"], {"get": {
                    "content": self.MOCK_GET_RESOURCE_RESPONSE}}),
            get_mock_session(
                ["post"], {"post": {
                    "content": self.MOCK_POST_RESOURCE_RESPONSE,
                    "status_code": 202}}),
        ]

        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        response = self.client.post(
            self.url, {}, HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        context = response.json()
        self.assertIn('error', context)
        self.assertEquals(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            response.status_code)

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_delete_resource(
            self, mock_get_vim_info, mock_get_session):

        mock_get_session.side_effect = [
            get_mock_session(
                ["delete"], {"delete": {"content": {},
                                        "status_code": 204}})
        ]

        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO

        response = self.client.delete(
            self.url + "/uuid_1",
            HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        self.assertEqual(status.HTTP_204_NO_CONTENT,
                         response.status_code)
        self.assertIsNone(response.data)
