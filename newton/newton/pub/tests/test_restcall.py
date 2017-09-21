# Copyright (c) 2017 Intel Corporation.
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

import sys
import traceback

from httplib2 import Http
import mock
from rest_framework import status
import unittest


from newton.pub.utils import restcall

class TestRestCall(unittest.TestCase):
    base_url = "http://localhost"
    resource = "compute"

    @mock.patch.object(Http, 'request')
    def test_failures_call_req(self, mock_http):
        mock_http.return_value = Exception('Test')
        traceback.format_exc = mock.Mock(return_value="")
        sys.exc_info = mock.Mock(return_value=("test", "", ""))
        args = [
            self.base_url, "user", "password", "auth_type",
            self.resource, "get", {"extra": "test"}
        ]

        ret = restcall._call_req(*args)
        self.assertEquals(3, ret[0])
        self.assertEquals(status.HTTP_500_INTERNAL_SERVER_ERROR, ret[2])

        sys.exc_info = mock.Mock(return_value=(
            'httplib.ResponseNotReady', None, None))

        ret = restcall._call_req(*args)
        self.assertEquals(1, ret[0])
        self.assertEquals("Unable to connect to %s" %
                          restcall._combine_url(
                              self.base_url, self.resource), ret[1])
        self.assertIsNone(ret[2])

        mock_http.return_value = ({'status': None}, "test")

        ret = restcall._call_req(*args)
        self.assertEquals(1, ret[0])
        self.assertEquals("test", ret[1])
        self.assertIsNone(ret[2])

    @mock.patch.object(Http, 'request')
    def test_req_by_msb(self, mock_http):
        resp_body="test_body".encode('UTF-8')
        resp_status=status.HTTP_200_OK
        mock_http.return_value = ({'status': resp_status}, resp_body)

        ret = restcall.req_by_msb(self.resource, "delete")
        self.assertEquals(0, ret[0])
        self.assertEquals(resp_body, ret[1])
        self.assertEquals(resp_status, ret[2])

    @mock.patch.object(Http, 'request')
    def test_req_to_vim(self, mock_http):
        resp_body="test_body".encode('UTF-8')
        resp_status=status.HTTP_200_OK
        mock_http.return_value = ({'status': resp_status}, resp_body)

        ret = restcall.req_to_vim(self.base_url, self.resource, "get")
        self.assertEquals(0, ret[0])
        self.assertEquals(resp_body, ret[1])
        self.assertEquals(resp_status, ret[2])

    @mock.patch.object(Http, 'request')
    def test_req_to_aai(self, mock_http):
        resp_body = "test_body".encode('UTF-8')
        resp_status = status.HTTP_200_OK
        mock_http.return_value = ({'status': resp_status}, resp_body)

        ret = restcall.req_to_aai(self.resource, "post")
        self.assertEquals(0, ret[0])
        self.assertEquals(resp_body, ret[1])
        self.assertEquals(resp_status, ret[2])

    def test_combine_url(self):
        self.assertEquals(self.base_url,
                          restcall._combine_url(self.base_url, ""))
        self.assertEquals(self.base_url + "/" + self.resource,
                          restcall._combine_url(self.base_url + "/",
                                               "/" + self.resource))
        self.assertEquals(self.base_url + "/" + self.resource,
                          restcall._combine_url(self.base_url + "/",
                                               self.resource))
        self.assertEquals(self.base_url + "/" + self.resource,
                          restcall._combine_url(self.base_url,
                                               "/" + self.resource))
        self.assertEquals(self.base_url + "/" + self.resource,
                          restcall._combine_url(self.base_url,
                                               self.resource))
