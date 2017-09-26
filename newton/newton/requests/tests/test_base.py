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
import unittest

from django.test import Client

MOCK_TOKEN_ID = "1a62b3971d774404a504c5d9a3e506e3"


class MockResponse(object):
    status_code = status.HTTP_200_OK
    content = ''

    def json(self):
        pass


def get_mock_session(http_actions, response_dict={}):
    mock_session = mock.Mock(
        name='mock_session',spec=http_actions)
    mock_response_obj = mock.Mock(spec=MockResponse)
    for action in http_actions:
        mock_response_obj.content = response_dict.get(
            action).get("content")
        mock_response_obj.json.return_value = response_dict.get(
            action).get("content")
        mock_response_obj.status_code = response_dict.get(
            action).get("status_code", status.HTTP_200_OK)
        if action == "get":
            mock_session.get.return_value = mock_response_obj
        if action == "post":
            mock_session.post.return_value = mock_response_obj
        if action == "put":
            mock_session.put.return_value = mock_response_obj
        if action == "delete":
            mock_session.delete.return_value = mock_response_obj
        if action == "head":
            mock_session.head.return_value = mock_response_obj

    return mock_session


class TestRequest(unittest.TestCase):

    def setUp(self):
        self.client = Client()
