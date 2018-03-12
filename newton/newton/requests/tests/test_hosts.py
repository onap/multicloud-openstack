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

from newton_base.tests.test_base import AbstractTestResource


class TestHostNewton(unittest.TestCase, AbstractTestResource):
    def setUp(self):
        AbstractTestResource.__init__(self)

        self.url += "hosts"

        self.MOCK_GET_RESOURCES_RESPONSE = {
            "hosts": [
            {"id": "uuid_1", "name": "host_1"},
            {"id": "uuid_2", "name": "host_2"}
            ]
        }

        self.MOCK_GET_RESOURCE_RESPONSE = {
            "host": [
                {"resource": {"id": "uuid_1", "name": "host_1"}}
            ]
        }

        self.MOCK_GET_RESOURCE_RESPONSE_NOT_FOUND = {}

        self.assert_keys = "hosts"
        self.assert_key = "host"

        self.HTTP_not_found = status.HTTP_500_INTERNAL_SERVER_ERROR

    # Overridden methods from test base to not make it run for current test case.
    def test_post_resource(self):
        pass

    def test_post_resource_existing(self):
        pass

    def test_post_resource_empty(self):
        pass

    def test_delete_resource(self):
        pass
