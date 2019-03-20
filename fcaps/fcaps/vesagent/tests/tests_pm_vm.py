# Copyright (c) 2019, CMCC Technologies Co., Ltd.
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
import json

from fcaps.vesagent import vespublish
from common.utils import restcall
from fcaps.vesagent.event_domain import pm_vm

MOCK_TOKEN_RESPONSE = {
    "access":
        {"token": {"issued_at": "2018-05-10T16:56:56.000000Z",
                   "expires": "2018-05-10T17:56:56.000000Z",
                   "id": "4e481914244d4adbb755c4ea455abff7",
                   "tenant": {"domain": {"id": "default", "name": "Default"},
                              "enabled": "true", "id": "9ef561bd76254639b8e31eea4b56f179", "name": "onap-casablanca01"}},
         "serviceCatalog": [], "user": {"domain": {"id": "default", "name": "Default"},
                                        "id": "ba76c94eb5e94bb7bec6980e5507aae2", "name": "demo"}}
}

MOCK_SERVERS_GET_RESPONSE = {
[
    {
        "user_id": "f0c15ff6b18044649d8877e81c8a6940",
        "resource_id": "012a5f3b-1c55-48bc-a606-951421c9a998",
        "timestamp": "2019-03-18T10:03:38",
        "meter": "cpu",
        "volume": 22771644070000000,
        "source": "openstack",
        "recorded_at": "2019-03-18T00:03:38",
        "project_id": "9ef561bd76254639b8e31eea4b56f179",
        "type": "cumulative",
        "id": "1a24800c-4965-11e9-acca-340a98d7c525",
        "unit": "ns",
        "metadata": {
            "instance_host": "compute-0",
            "ephemeral_gb": "0",
            "flavor.vcpus": "16",
            "OS-EXT-AZ.availability_zone": "nova",
            "memory_mb": "65536",
            "task_state": "None",
            "display_name": "mr01-node5",
            "state": "active",
            "flavor.ram": "65536",
            "status": "active",
            "ramdisk_id": "None",
            "flavor.name": "oom.mr.xlarge",
            "disk_gb": "200",
            "kernel_id": "None",
            "image.id": "16d5044e-fbd7-4608-8883-b3028298e0db",
            "flavor.id": "d74dfa1c-b57d-4cb3-86a7-3c80ea896364",
            "host": "24c567dfb69e92bb1118d1dff0ecd163e20c02b5ce7c5ce7b639d0a0",
            "vcpu_number": "1",
            "image.name": "ubuntu_16.04",
            "image_ref_url": "http://msb-iag.onap:80/api/multicloud-titaniumcloud/v1/CloudOwner3/RegionOne/compute/196f992027c640f292de1c1397ad5858/images/16d5044e-fbd7-4608-8883-b3028298e0db",
            "name": "instance-000000ea",
            "cpu_number": "16",
            "flavor.disk": "200",
            "root_gb": "200",
            "image.links": "[{'href': 'http://msb-iag.onap:80/api/multicloud-titaniumcloud/v1/CloudOwner3/RegionOne/compute/196f992027c640f292de1c1397ad5858/images/16d5044e-fbd7-4608-8883-b3028298e0db', 'rel': 'bookmark'}]",
            "flavor.ephemeral": "0",
            "instance_id": "012a5f3b-1c55-48bc-a606-951421c9a998",
            "instance_type": "oom.mr.xlarge",
            "vcpus": "16",
            "image_ref": "16d5044e-fbd7-4608-8883-b3028298e0db",
            "flavor.links": "[{'href': 'http://msb-iag.onap:80/api/multicloud-titaniumcloud/v1/CloudOwner3/RegionOne/compute/196f992027c640f292de1c1397ad5858/flavors/d74dfa1c-b57d-4cb3-86a7-3c80ea896364', 'rel': 'bookmark'}]"
        }
    },
    {
        "user_id": "f0c15ff6b18044649d8877e81c8a6940",
        "resource_id": "012a5f3b-1c55-48bc-a606-951421c9a998",
        "timestamp": "2019-03-18T09:53:12",
        "meter": "memory.usage",
        "volume": 62660,
        "source": "openstack",
        "recorded_at": "2019-03-18T00:53:12",
        "project_id": "9ef561bd76254639b8e31eea4b56f179",
        "type": "gauge",
        "id": "a47d3cfa-4963-11e9-acca-340a98d7c525",
        "unit": "MB",
        "metadata": {
            "instance_host": "compute-0",
            "ephemeral_gb": "0",
            "flavor.vcpus": "16",
            "OS-EXT-AZ.availability_zone": "nova",
            "instance_id": "012a5f3b-1c55-48bc-a606-951421c9a998",
            "task_state": "None",
            "display_name": "mr01-node5",
            "state": "active",
            "flavor.ram": "65536",
            "status": "active",
            "ramdisk_id": "None",
            "flavor.name": "oom.mr.xlarge",
            "disk_gb": "200",
            "kernel_id": "None",
            "image.id": "16d5044e-fbd7-4608-8883-b3028298e0db",
            "flavor.id": "d74dfa1c-b57d-4cb3-86a7-3c80ea896364",
            "host": "24c567dfb69e92bb1118d1dff0ecd163e20c02b5ce7c5ce7b639d0a0",
            "flavor.ephemeral": "0",
            "image.name": "ubuntu_16.04",
            "image_ref_url": "http://msb-iag.onap:80/api/multicloud-titaniumcloud/v1/CloudOwner3/RegionOne/compute/196f992027c640f292de1c1397ad5858/images/16d5044e-fbd7-4608-8883-b3028298e0db",
            "name": "instance-000000ea",
            "flavor.disk": "200",
            "root_gb": "200",
            "image.links": "[{'href': 'http://msb-iag.onap:80/api/multicloud-titaniumcloud/v1/CloudOwner3/RegionOne/compute/196f992027c640f292de1c1397ad5858/images/16d5044e-fbd7-4608-8883-b3028298e0db', 'rel': 'bookmark'}]",
            "memory_mb": "65536",
            "instance_type": "oom.mr.xlarge",
            "vcpus": "16",
            "image_ref": "16d5044e-fbd7-4608-8883-b3028298e0db",
            "flavor.links": "[{'href': 'http://msb-iag.onap:80/api/multicloud-titaniumcloud/v1/CloudOwner3/RegionOne/compute/196f992027c640f292de1c1397ad5858/flavors/d74dfa1c-b57d-4cb3-86a7-3c80ea896364', 'rel': 'bookmark'}]"
        }
    }
 ]
}

MOCK_BACKLOG_INPUT = {
    "backlog_uuid": "ce2d7597-22e1-4239-890f-bc303bd67076",
    "server_id": "012a5f3b-1c55-48bc-a606-951421c9a998",
    "tenant_id": "0e148b76ee8c42f78d37013bf6b7b1ae", "api_method": "GET",
    "source": "onap-aaf",
    "api_link":
        "/onaplab_RegionOne/compute/v2.1/0e148b76ee8c42f78d37013bf6b7b1ae/servers/c4b575fa-ed85-4642-ab4b-335cb5744721",
    "domain": "pm", "type": "vm", "tenant": "VIM"
}

MOCK_BACKLOG_INPUT_wo_tenant_id = {
    "backlog_uuid": "ce2d7597-22e1-4239-890f-bc303bd67076",
    "server_id": "012a5f3b-1c55-48bc-a606-951421c9a998",
    "source": "onap-aaf",
    "api_link":
        "/onaplab_RegionOne/compute/v2.1/0e148b76ee8c42f78d37013bf6b7b1ae/servers/c4b575fa-ed85-4642-ab4b-335cb5744721",
    "domain": "pm", "type": "vm", "tenant": "VIM"
}

MOCK_BACKLOG_INPUT_wo_tenant = {
    "backlog_uuid": "ce2d7597-22e1-4239-890f-bc303bd67076",
    "server_id": "012a5f3b-1c55-48bc-a606-951421c9a998",
    "source": "onap-aaf",
    "domain": "fault", "type": "vm", }

MOCK_BACKLOG_INPUT_wo_server_id = {
    "source": "onap-aaf",
    "domain": "fault", "type": "vm", "tenant": "VIM"}

MOCK_BACKLOG_INPUT_wo_server = {"domain": "pm", "type": "vm", "tenant": "VIM"}

MOCK_SERVER_GET_RESPONSE = {
    "server": {"wrs-res:topology": "node:0,  4096MB, pgsize:2M, vcpus:0,1, pol:sha",
               "OS-EXT-STS:task_state": None,
               "addresses": {
                   "oam_onap_BTHY": [{"OS-EXT-IPS-MAC:mac_addr": "fa:16:3e:6c:0d:6b",
                                      "version": 4, "addr": "10.0.13.1", "OS-EXT-IPS:type": "fixed"},
                                     {"OS-EXT-IPS-MAC:mac_addr": "fa:16:3e:6c:0d:6b", "version": 4,
                                      "addr": "10.12.5.185", "OS-EXT-IPS:type": "floating"}]},
               "links": [], "image": {"id": "6e219e86-cd94-4989-9119-def29aa10b12", "links": []},
               "wrs-if:nics": [], "wrs-sg:server_group": "",
               "OS-EXT-STS:vm_state": "active", "OS-SRV-USG:launched_at": "2018-04-26T08:01:28.000000",
               "flavor": {}, "id": "c4b575fa-ed85-4642-ab4b-335cb5744721",
               "security_groups": [{"name": "onap_sg_BTHY"}],
               "user_id": "ba76c94eb5e94bb7bec6980e5507aae2",
               "OS-DCF:diskConfig": "MANUAL", "accessIPv4": "",
               "accessIPv6": "", "progress": 0, "OS-EXT-STS:power_state": 1,
               "OS-EXT-AZ:availability_zone": "nova", "metadata": {},
               "status": "ACTIVE", "updated": "2018-04-26T08:01:28Z",
               "hostId": "17acc9f2ae4f618c314e4cdf0c206585b895bc72a9ec57e57b254133",
               "OS-SRV-USG:terminated_at": None, "wrs-res:pci_devices": "",
               "wrs-res:vcpus": [2, 2, 2], "key_name": "onap_key_BTHY", "name": "onap-aaf",
               "created": "2018-04-26T08:01:20Z", "tenant_id": "0e148b76ee8c42f78d37013bf6b7b1ae",
               "os-extended-volumes:volumes_attached": [], "config_drive": ""}}

MOCK_SERVER_GET_RESPONSE_empty = {}

MOCK_vesAgentConfig = {
    "backlogs": [
        {"backlog_uuid": "ce2d7597-22e1-4239-890f-bc303bd67076",
         "server_id": "012a5f3b-1c55-48bc-a606-951421c9a998",
         "tenant_id": "0e148b76ee8c42f78d37013bf6b7b1ae", "api_method": "GET",
         "source": "onap-aaf",
         "api_link":
             "/onaplab_RegionOne/compute/v2.1/0e148b76ee8c42f78d37013bf6b7b1ae/servers/c4b575fa-ed85-4642-ab4b-335cb5744721",
         "domain": "fault", "type": "vm", "tenant": "VIM"}
    ],
    "poll_interval_default": 10, "vimid": "CloudOwner3_RegionOne",
    "ves_subscription": {"username": "user", "password": "password",
                         "endpoint": "http://127.0.0.1:9011/sample"}}

MOCK_vesAgentState = {"ce2d7597-22e1-4239-890f-bc303bd67076": {"timestamp": 1525975400}}
MOCK_oneBacklog = {
    "backlog_uuid": "ce2d7597-22e1-4239-890f-bc303bd67076",
    "server_id": "012a5f3b-1c55-48bc-a606-951421c9a998",
    "tenant_id": "0e148b76ee8c42f78d37013bf6b7b1ae",
    "api_method": "GET", "source": "onap-aaf",
    "api_link":
        "/onaplab_RegionOne/compute/v2.1/0e148b76ee8c42f78d37013bf6b7b1ae/servers/c4b575fa-ed85-4642-ab4b-335cb5744721",
    "domain": "fault", "type": "vm", "tenant": "VIM"}


class PmVMTest(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_epoch_now_usecond(self):
        epoch = pm_vm.get_epoch_now_usecond()
        self.assertGreater(epoch, 1)

    @mock.patch.object(restcall, '_call_req')
    def test_buildBacklog_pm_vm(self, mock_call_req):
        mock_call_req.side_effect = [
            (0, json.dumps(MOCK_TOKEN_RESPONSE), "MOCKED response body"),
            (0, json.dumps(MOCK_SERVERS_GET_RESPONSE), "MOCKED response body")
        ]
        backlog = pm_vm.buildBacklog_pm_vm(
            vimid="CloudOwner3_RegionOne",
            backlog_input=MOCK_BACKLOG_INPUT)

        self.assertIsNotNone(backlog)
