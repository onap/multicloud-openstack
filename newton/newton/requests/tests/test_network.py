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

import unittest

from rest_framework import status

from newton.requests.tests.test_base import AbstractTestResource


class TestNetworkNewton(unittest.TestCase, AbstractTestResource):
    def setUp(self):
        AbstractTestResource.__init__(self)

        self.url += "networks"

        self.MOCK_GET_RESOURCES_RESPONSE = {
            "networks": [
                {"name": "network_1"},
                {"name": "network_2"}
            ]
        }

        self.MOCK_GET_RESOURCE_RESPONSE = {
            "network": {
            "id": "f5dc173b-6804-445a-a6d8-c705dad5b5eb",
            "name": "network_3"
            }
        }

        self.MOCK_GET_RESOURCE_RESPONSE_NOT_FOUND = {}

        self.MOCK_POST_RESOURCE_REQUEST = {
            "name": "network_3"
        }

        self.MOCK_POST_RESOURCE_REQUEST_EXISTING = {
            "name": "network_1"
        }

        self.MOCK_POST_RESOURCE_RESPONSE = {
            "network": {
            "id": "f5dc173b-6804-445a-a6d8-c705dad5b5eb"
            }
        }

        self.assert_keys = "networks"
        self.assert_key = "id"

        self.HTTP_not_found = status.HTTP_500_INTERNAL_SERVER_ERROR
