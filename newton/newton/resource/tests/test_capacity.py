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
import json

from rest_framework import status

from common.utils import restcall
from newton_base.tests import mock_info
from newton_base.tests import test_base
from newton_base.util import VimDriverUtils

MOCK_GET_TENANT_LIMIT_RESPONSE = {
   "limits" : {
      "rate" : [],
      "absolute" : {
         "maxTotalRAMSize" : 128*1024,
         "totalRAMUsed" : 8*1024,
         "totalCoresUsed" : 4,
         "maxTotalCores" : 20,
      }
   }
}

MOCK_GET_HYPER_STATATICS_RESPONSE = {
   "hypervisor_statistics" : {
      "vcpus_used" : 4,
      "free_ram_mb" : 120*1024,
      "vcpus" : 10,
      "free_disk_gb" : 300
   }
}

MOCK_GET_HYPER_STATATICS_RESPONSE_OUTOFVCPU = {
    "hypervisor_statistics": {
        "vcpus_used": 9,
        "free_ram_mb": 120 * 1024,
        "vcpus": 10,
        "free_disk_gb": 300
    }
}

MOCK_GET_HYPER_STATATICS_RESPONSE_OUTOFSTORAGE = {
   "hypervisor_statistics" : {
      "vcpus_used" : 4,
      "free_ram_mb" : 120*1024,
      "vcpus" : 10,
      "free_disk_gb" : 3
   }
}

MOCK_GET_HYPER_STATATICS_RESPONSE_OUTOFRAM = {
   "hypervisor_statistics" : {
      "vcpus_used" : 4,
      "free_ram_mb" : 1*1024,
      "vcpus" : 10,
      "free_disk_gb" : 300
   }
}

MOCK_GET_STORAGE_RESPONSE = {
   "limits" : {
      "rate" : [],
      "absolute" : {
         "totalGigabytesUsed" : 200,
         "maxTotalVolumeGigabytes" : 500,
      }
   }
}

TEST_REQ_SUCCESS_SOURCE = {
    "vCPU": "4",
    "Memory": "4096",
    "Storage": "200"
}

TEST_REQ_FAILED_SOURCE = {
    "vCPU": "17",
    "Memory": "4096",
    "Storage": "200"
}

class TestCapacity(test_base.TestRequest):
    def setUp(self):
        super(TestCapacity, self).setUp()

    def _get_mock_response(self, return_value=None):
        mock_response = mock.Mock(spec=test_base.MockResponse)
        mock_response.status_code = status.HTTP_200_OK
        mock_response.json.return_value = return_value
        return mock_response

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_capacity_check_success(self, mock_get_vim_info, mock_get_session):
        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO
        mock_get_session.return_value = test_base.get_mock_session(
            ["get"], {
                "side_effect": [
                    self._get_mock_response(MOCK_GET_TENANT_LIMIT_RESPONSE),
                    self._get_mock_response(MOCK_GET_HYPER_STATATICS_RESPONSE),
                    self._get_mock_response(MOCK_GET_STORAGE_RESPONSE),
                ]
            })

        response = self.client.post(
            "/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne/capacity_check",
            TEST_REQ_SUCCESS_SOURCE,
            HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertEqual({"result": True}, response.data)

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_capacity_check_nova_limits_failed(self, mock_get_vim_info, mock_get_session):
        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO
        mock_get_session.return_value = test_base.get_mock_session(
            ["get"], {
                "side_effect": [
                    self._get_mock_response(MOCK_GET_TENANT_LIMIT_RESPONSE),
                    self._get_mock_response(MOCK_GET_HYPER_STATATICS_RESPONSE),
                    self._get_mock_response(MOCK_GET_STORAGE_RESPONSE),
                ]
            })

        response = self.client.post(
            "/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne/capacity_check",
            TEST_REQ_FAILED_SOURCE,
            HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertEqual({"result": False}, response.data)

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_capacity_check_nova_hypervisor_outofram(self, mock_get_vim_info, mock_get_session):
        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO
        mock_get_session.return_value = test_base.get_mock_session(
            ["get"], {
                "side_effect": [
                    self._get_mock_response(MOCK_GET_TENANT_LIMIT_RESPONSE),
                    self._get_mock_response(MOCK_GET_HYPER_STATATICS_RESPONSE_OUTOFRAM),
                    self._get_mock_response(MOCK_GET_STORAGE_RESPONSE),
                ]
            })

        response = self.client.post(
            "/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne/capacity_check",
            data=json.dumps(TEST_REQ_SUCCESS_SOURCE),
            content_type='application/json',
            HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertEqual({"result": False}, response.data)

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_capacity_check_nova_hypervisor_outofstorage(self, mock_get_vim_info, mock_get_session):
        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO
        mock_get_session.return_value = test_base.get_mock_session(
            ["get"], {
                "side_effect": [
                    self._get_mock_response(MOCK_GET_TENANT_LIMIT_RESPONSE),
                    self._get_mock_response(MOCK_GET_HYPER_STATATICS_RESPONSE_OUTOFSTORAGE),
                    self._get_mock_response(MOCK_GET_STORAGE_RESPONSE),
                ]
            })

        response = self.client.post(
            "/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne/capacity_check",
            data=json.dumps(TEST_REQ_SUCCESS_SOURCE),
            content_type='application/json',
            HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertEqual({"result": False}, response.data)

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_capacity_check_nova_hypervisor_outofvcpu(self, mock_get_vim_info, mock_get_session):
        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO
        mock_get_session.return_value = test_base.get_mock_session(
            ["get"], {
                "side_effect": [
                    self._get_mock_response(MOCK_GET_TENANT_LIMIT_RESPONSE),
                    self._get_mock_response(MOCK_GET_HYPER_STATATICS_RESPONSE_OUTOFVCPU),
                    self._get_mock_response(MOCK_GET_STORAGE_RESPONSE),
                ]
            })

        response = self.client.post(
            "/api/multicloud-newton/v0/windriver-hudson-dc_RegionOne/capacity_check",
            data=json.dumps(TEST_REQ_SUCCESS_SOURCE),
            content_type='application/json',
            HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertEqual({"result": False}, response.data)

