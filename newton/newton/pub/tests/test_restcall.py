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

from httplib2 import Http
import mock
from rest_framework import status
import unittest

from newton.pub.utils import restcall

rest_no_auth, rest_oneway_auth, rest_bothway_auth = 0, 1, 2

class TestRestCall(unittest.TestCase):
    base_url = "http://localhost"
    resource = "compute"

    @mock.patch.object(Http, 'request')
    def test_unknown_failure_call_req(self, mock_http):
        mock_http.raiseError.side_effect = mock.Mock(
            side_effect=Exception('Test'))
        args = [
            self.base_url, None, None, rest_no_auth,
            self.resource, "get", {"extra": "test"}
        ]

        ret = restcall._call_req(*args)
        self.assertEquals(3, ret[0])
        self.assertEquals(status.HTTP_500_INTERNAL_SERVER_ERROR, ret[2])


    @mock.patch.object(Http, 'request')
    def test_invalid_output_call_req(self, mock_http):
        args = [
            self.base_url, None, None, rest_no_auth,
            self.resource, "get", {"extra": "test"}
        ]

        mock_http.return_value = ({'status': None},
                                  str.encode("test", 'utf-8'))

        ret = restcall._call_req(*args)
        self.assertEquals(1, ret[0])
        self.assertEquals("test", ret[1])
        self.assertIsNone(ret[2])

    @mock.patch.object(Http, 'request')
    def test_req_by_msb(self, mock_http):
        resp_body = "test_body"
        resp_status='200' #status.HTTP_200_OK
        mock_http.return_value = (
            {'status': resp_status},
            str.encode(resp_body, 'utf-8'))


        ret = restcall.req_by_msb(self.resource, "delete")
        self.assertEquals(0, ret[0])
        self.assertEquals(resp_body, ret[1])
        self.assertEquals(resp_status, ret[2])

    @mock.patch.object(Http, 'request')
    def test_req_to_vim(self, mock_http):
        resp_body = "test_body"
        resp_status='200' #status.HTTP_200_OK
        mock_http.return_value = (
            {'status': resp_status},
            str.encode(resp_body, 'utf-8'))

        ret = restcall.req_to_vim(self.base_url, self.resource, "get")
        self.assertEquals(0, ret[0])
        self.assertEquals(resp_body, ret[1])
        self.assertEquals(resp_status, ret[2])

    @mock.patch.object(Http, 'request')
    def test_req_to_aai(self, mock_http):
        resp_body = "test_body"
        resp_status='200' #status.HTTP_200_OK
        mock_http.return_value = (
            {'status': resp_status},
            str.encode(resp_body, 'utf-8'))

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
