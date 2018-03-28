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

from common.utils import restcall
from newton_base.tests import mock_info
from newton_base.tests import test_base
from newton_base.util import VimDriverUtils

MOCK_GET_TENANT_RESPONSE = {
    "projects":[
        {"id": "1", "name": "project"},
        {"id": "2", "name": "project2"},
    ]
}

MOCK_GET_FLAVOR_RESPONSE = {
    "flavors": [
        {
            "id": "1", "name": "micro", "vcpus": 1, "ram": "1MB",
            "disk": "1G", "OS-FLV-EXT-DATA:ephemeral": False,
            "swap": True, "os-flavor-access:is_public": True,
            "OS-FLV-DISABLED:disabled": True, "link": [{"href":1}]
         },
        {
            "id": "2", "name": "mini", "vcpus": 2, "ram": "2MB",
            "disk": "2G", "OS-FLV-EXT-DATA:ephemeral": True,
            "swap": False, "os-flavor-access:is_public": True,
            "OS-FLV-DISABLED:disabled": True
        },
    ]
}

MOCK_GET_IMAGE_RESPONSE = {
    "images": [
        {
            "id": "1", "name": "cirros", "self": "test",
            "os_distro": "CirrOS", "os_version": "0.3",
            "application": "test", "application_vendor": "ONAP",
            "application_version": 1, "architecture": "x86",
            "schema": None
        },
        {
            "id": "2", "name": "cirros", "self": "test",
            "os_distro": "CirrOS", "os_version": "0.3",
            "application": "test", "application_vendor": "ONAP",
            "application_version": 1, "architecture": "x86",
            "schema": "req_resource"
        },
    ]
}

MOCK_GET_AZ_RESPONSE = {
    "availabilityZoneInfo": [
        {
            "zoneName": "production",
            "zoneState": {"available": True},
            "hosts": { "hypervisor": "kvm" }
        },
        {
            "zoneName": "testing",
        },
    ]
}

MOCK_HYPERVISOR_RESPONSE = {
    "hypervisors": [
        {"hypervisor_type": "kvm"}
    ]
}

MOCK_GET_SNAPSHOT_RESPONSE = {
    "snapshots": [
        {
            "id": 1, "name": "test", "metadata":
            {
            "architecture": "x86", "os-distro": "clearlinux",
            "os-version": "276", "vendor": "intel", "version": 3,
            "selflink": "test", "prev-snapshot-id": "test-id"
            }
        },
        {"id": 2, "name": "test2"}
    ]
}

MOCK_GET_HYPERVISOR_RESPONSE = {
    "hypervisors": [
        {
            "hypervisor_hostname": "testing", "state": "ACTIVE",
            "id": 1, "local_gb": 256, "memory_mb": 1024,
            "hypervisor_links": "link", "host_ip": "127.0.0.1",
            "cpu_info": u'{"topology": {"cores": 8, "threads": 16, "sockets": 4}}'
        },
        {
            "hypervisor_hostname": "testing2", "state": "XXX",
            "id": 1, "local_gb": 256, "memory_mb": 1024,
            "hypervisor_links": "link", "host_ip": "127.0.0.1",
        }
    ]
}

TEST_REGISTER_ENDPOINT_REQUEST = {
    "defaultTenant": "project1"
}



class TestRegistration(test_base.TestRequest):

    def setUp(self):
        super(TestRegistration, self).setUp()
        self.req_to_aai_backup = restcall.req_to_aai

    def tearDown(self):
        super(TestRegistration, self).tearDown()
        restcall.req_to_aai = self.req_to_aai_backup

    def _get_mock_response(self, return_value=None):
        mock_response = mock.Mock(spec=test_base.MockResponse)
        mock_response.status_code = status.HTTP_200_OK
        mock_response.json.return_value = return_value
        return mock_response

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_register_endpoint_successfully(
            self, mock_get_vim_info, mock_get_session):
        restcall.req_to_aai = mock.Mock()
        restcall.req_to_aai.return_value = (0, {}, status.HTTP_200_OK)
        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO
        mock_get_session.return_value = test_base.get_mock_session(
            ["get"], {
                "side_effect": [
                    self._get_mock_response(MOCK_GET_TENANT_RESPONSE),
                    self._get_mock_response(MOCK_GET_FLAVOR_RESPONSE),
                    self._get_mock_response(MOCK_GET_IMAGE_RESPONSE),
                    self._get_mock_response(),
                    self._get_mock_response(MOCK_GET_AZ_RESPONSE),
                    self._get_mock_response(MOCK_HYPERVISOR_RESPONSE),
                    self._get_mock_response(MOCK_GET_SNAPSHOT_RESPONSE),
                    self._get_mock_response(MOCK_GET_HYPERVISOR_RESPONSE)
                ]
            })

        response = self.client.post((
            "/api/multicloud-titanium_cloud/v0/windriver-hudson-dc_RegionOne/"
            "registry"), TEST_REGISTER_ENDPOINT_REQUEST,
            HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        self.assertEquals(status.HTTP_202_ACCEPTED,
                          response.status_code)

    @mock.patch.object(VimDriverUtils, 'delete_vim_info')
    def test_unregister_endpoint_successfully(
            self, mock_delete_vim_info):
        mock_delete_vim_info.return_value = 0

        response = self.client.delete((
            "/api/multicloud-titanium_cloud/v0/windriver-hudson-dc_RegionOne/"
            "registry"), "{}", content_type="application/json",
            HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        self.assertEquals(status.HTTP_202_ACCEPTED,
                          response.status_code)


    @mock.patch.object(VimDriverUtils, 'delete_vim_info')
    def test_fail_unregister_endpoint(
            self, mock_delete_vim_info):
        mock_delete_vim_info.return_value = 1

        response = self.client.delete((
            "/api/multicloud-titanium_cloud/v0/windriver-hudson-dc_RegionOne/"
            "registry"), "{}", content_type="application/json",
            HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        self.assertEquals(status.HTTP_500_INTERNAL_SERVER_ERROR,
                          response.status_code)



# HPA UT1: CPU-PINNING
MOCK_GET_HPA_FLAVOR_LIST1_RESPONSE= {
    "flavors": [
        {
            "id": "1", "name": "micro", "vcpus": 1, "ram": "1MB",
            "disk": "1G", "OS-FLV-EXT-DATA:ephemeral": False,
            "swap": True, "os-flavor-access:is_public": True,
            "OS-FLV-DISABLED:disabled": True, "link": [{"href": 1}]
        },
        {
            "id": "2", "name": "onap.mini", "vcpus": 2, "ram": "2MB",
            "disk": "2G", "OS-FLV-EXT-DATA:ephemeral": True,
            "swap": False, "os-flavor-access:is_public": True,
            "OS-FLV-DISABLED:disabled": True
        },
    ]
}

MOCK_GET_HPA_FLAVOR_onap_mini_EXTRA_SPECS_RESPONSE = {
    "extra_specs": {
        "aggregate_instance_extra_specs:storage": "local_image",
        "capabilities:cpu_info:model": "Haswell",
        "hw:cpu_policy": "dedicated",
        "hw:cpu_thread_policy": "prefer"
    }
}

@mock.patch.object(VimDriverUtils, 'get_session')
@mock.patch.object(VimDriverUtils, 'get_vim_info')
def test_register_hpa_cpupinning_successfully(
        self, mock_get_vim_info, mock_get_session):
    restcall.req_to_aai = mock.Mock()
    restcall.req_to_aai.return_value = (0, {}, status.HTTP_200_OK)
    mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO
    mock_get_session.return_value = test_base.get_mock_session(
        ["get"], {
            "side_effect": [
                self._get_mock_response(MOCK_GET_TENANT_RESPONSE),
                self._get_mock_response(MOCK_GET_HPA_FLAVOR_LIST1_RESPONSE),
                self._get_mock_response(MOCK_GET_HPA_FLAVOR_onap_mini_EXTRA_SPECS_RESPONSE),
                self._get_mock_response(MOCK_GET_IMAGE_RESPONSE),
                self._get_mock_response(),
                self._get_mock_response(MOCK_GET_AZ_RESPONSE),
                self._get_mock_response(MOCK_HYPERVISOR_RESPONSE),
                self._get_mock_response(MOCK_GET_SNAPSHOT_RESPONSE),
                self._get_mock_response(MOCK_GET_HYPERVISOR_RESPONSE)
            ]
        })

    response = self.client.post((
        "/api/multicloud-titanium_cloud/v0/windriver-hudson-dc_RegionOne/"
        "registry"), TEST_REGISTER_ENDPOINT_REQUEST,
        HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

    self.assertEquals(status.HTTP_202_ACCEPTED,
                      response.status_code)

