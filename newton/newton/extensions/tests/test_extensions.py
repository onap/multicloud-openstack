# Copyright 2017-2018 Wind River Systems, Inc.
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

from django.test import Client
from rest_framework import status
import unittest

from newton.requests.tests import test_base


class TestExtensions(unittest.TestCase):
    def setUp(self):
        self.client = Client()

    def test_get_extensions_info(self):
        cloud_owner = "windriver-hudson-dc"
        cloud_region_id = "RegionOne"
        vimid = cloud_owner + "_" + cloud_region_id

        response = self.client.get(
            "/api/%s/v0/%s/extensions/" % (
                test_base.MULTIVIM_VERSION, vimid))
        json_content = response.json()

        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertEquals(4, len(json_content.keys()))

        self.assertEquals(cloud_owner, json_content["cloud-owner"])
        self.assertEquals(cloud_region_id,
                          json_content["cloud-region-id"])
        self.assertEquals(vimid, json_content["vimid"])

        self.assertEquals("epa-caps",
                          json_content["extensions"][0]["alias"])
        self.assertEquals("Multiple network support",
                          json_content["extensions"][0][
                              "description"])
        self.assertEquals("EPACapsQuery",
                          json_content["extensions"][0]["name"])
        self.assertEquals(
            "http://127.0.0.1:80/api/%s/v0/%s/extensions/epa-caps" % (
                test_base.MULTIVIM_VERSION, vimid),
            json_content["extensions"][0]["url"])
        self.assertEquals("", json_content["extensions"][0]["spec"])
