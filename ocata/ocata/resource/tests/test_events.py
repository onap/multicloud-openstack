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

MOCK_GET_SERVERS_DETAIL_RESPONSE = {
   "servers" : [
      {
         "accessIPv4" : "",
         "OS-EXT-SRV-ATTR:instance_name" : "instance-0000000a",
         "OS-SRV-USG:terminated_at" : "",
         "accessIPv6" : "",
         "config_drive" : "",
         "OS-DCF:diskConfig" : "AUTO",
         "updated" : "2018-03-27T02:17:12Z",
         "metadata" : {},
         "id" : "12f5b1d0-fe5c-469f-a7d4-b62a91134bf8",
         "flavor" : {
            "id" : "60edb520-5826-4ae7-9e07-709b19ba6f39",
            "links" : [
               {
                  "rel" : "bookmark",
                  "href" : "http://192.168.100.100:8774/ad979139d5ea4a84b21b3620c0e4761e/flavors/60edb520-5826-4ae7-9e07-709b19ba6f39"
               }
            ]
         },
         "links" : [
            {
               "rel" : "self",
               "href" : "http://192.168.100.100:8774/v2.1/ad979139d5ea4a84b21b3620c0e4761e/servers/12f5b1d0-fe5c-469f-a7d4-b62a91134bf8"
            },
            {
               "rel" : "bookmark",
               "href" : "http://192.168.100.100:8774/ad979139d5ea4a84b21b3620c0e4761e/servers/12f5b1d0-fe5c-469f-a7d4-b62a91134bf8"
            }
         ],
         "OS-EXT-SRV-ATTR:host" : "compute-0",
         "OS-EXT-AZ:availability_zone" : "nova",
         "name" : "test1",
         "wrs-res:pci_devices" : "",
         "hostId" : "b3479a460f5effda10c6fdb860e824be631026c1d09f551479180577",
         "user_id" : "777155411f3042c9b7e3194188d6f85d",
         "status" : "PAUSED",
         "OS-EXT-STS:power_state" : 3,
         "OS-EXT-SRV-ATTR:hypervisor_hostname" : "compute-0",
         "tenant_id" : "ad979139d5ea4a84b21b3620c0e4761e",
         "OS-SRV-USG:launched_at" : "2018-03-27T02:16:40.000000",
         "OS-EXT-STS:vm_state" : "paused",
         "wrs-if:nics" : [
            {
               "nic1" : {
                  "mac_address" : "fa:16:3e:5f:1a:76",
                  "network" : "mgmt",
                  "port_id" : "6c225c23-abe3-42a8-8909-83471503d5d4",
                  "vif_model" : "virtio",
                  "vif_pci_address" : "",
                  "mtu" : 9216
               }
            },
            {
               "nic2" : {
                  "mac_address" : "fa:16:3e:7c:7b:d7",
                  "network" : "data0",
                  "port_id" : "cbea2fec-c9b8-48ec-a964-0e3e255841bc",
                  "vif_model" : "virtio",
                  "vif_pci_address" : "",
                  "mtu" : 9216
               }
            }
         ],
         "wrs-sg:server_group" : "",
         "OS-EXT-STS:task_state" : "",
         "wrs-res:topology" : "node:0,  1024MB, pgsize:2M, 1s,1c,2t, vcpus:0,1, pcpus:5,21, siblings:{0,1}, pol:ded, thr:pre\nnode:1,  1024MB, pgsize:2M, 1s,1c,2t, vcpus:2,3, pcpus:8,24, siblings:{2,3}, pol:ded, thr:pre",
         "wrs-res:vcpus" : [
            4,
            4,
            4
         ],
         "key_name" : "",
         "image" : {
            "id" : "7ba636ef-5dfd-4e67-ad32-cd23ee74e1eb",
            "links" : [
               {
                  "rel" : "bookmark",
                  "href" : "http://192.168.100.100:8774/ad979139d5ea4a84b21b3620c0e4761e/images/7ba636ef-5dfd-4e67-ad32-cd23ee74e1eb"
               }
            ]
         },
         "created" : "2018-03-27T02:16:32Z",
         "addresses" : {
            "data0" : [
               {
                  "OS-EXT-IPS:type" : "fixed",
                  "version" : 4,
                  "OS-EXT-IPS-MAC:mac_addr" : "fa:16:3e:7c:7b:d7",
                  "addr" : "192.168.2.8"
               }
            ],
            "mgmt" : [
               {
                  "OS-EXT-IPS:type" : "fixed",
                  "version" : 4,
                  "OS-EXT-IPS-MAC:mac_addr" : "fa:16:3e:5f:1a:76",
                  "addr" : "192.168.1.6"
               }
            ]
         },
         "os-extended-volumes:volumes_attached" : []
      },
      {
         "accessIPv4" : "",
         "OS-EXT-SRV-ATTR:instance_name" : "instance-00000009",
         "OS-SRV-USG:terminated_at" : "",
         "accessIPv6" : "",
         "config_drive" : "",
         "OS-DCF:diskConfig" : "AUTO",
         "updated" : "2018-03-27T02:12:21Z",
         "metadata" : {},
         "id" : "3f1b0375-a1db-4d94-b336-f32c82c0d7ec",
         "flavor" : {
            "id" : "0d3b1381-1626-4f6b-869b-4a4d5d42085e",
            "links" : [
               {
                  "rel" : "bookmark",
                  "href" : "http://192.168.100.100:8774/ad979139d5ea4a84b21b3620c0e4761e/flavors/0d3b1381-1626-4f6b-869b-4a4d5d42085e"
               }
            ]
         },
         "links" : [
            {
               "rel" : "self",
               "href" : "http://192.168.100.100:8774/v2.1/ad979139d5ea4a84b21b3620c0e4761e/servers/3f1b0375-a1db-4d94-b336-f32c82c0d7ec"
            },
            {
               "rel" : "bookmark",
               "href" : "http://192.168.100.100:8774/ad979139d5ea4a84b21b3620c0e4761e/servers/3f1b0375-a1db-4d94-b336-f32c82c0d7ec"
            }
         ],
         "OS-EXT-SRV-ATTR:host" : "compute-0",
         "OS-EXT-AZ:availability_zone" : "nova",
         "name" : "test2",
         "wrs-res:pci_devices" : "",
         "hostId" : "b3479a460f5effda10c6fdb860e824be631026c1d09f551479180577",
         "user_id" : "777155411f3042c9b7e3194188d6f85d",
         "status" : "ACTIVE",
         "OS-EXT-STS:power_state" : 1,
         "OS-EXT-SRV-ATTR:hypervisor_hostname" : "compute-0",
         "tenant_id" : "ad979139d5ea4a84b21b3620c0e4761e",
         "OS-SRV-USG:launched_at" : "2018-03-27T02:12:21.000000",
         "OS-EXT-STS:vm_state" : "active",
         "wrs-if:nics" : [
            {
               "nic1" : {
                  "mac_address" : "fa:16:3e:54:f8:a6",
                  "network" : "mgmt",
                  "port_id" : "30e2f51c-4473-4650-9ae9-a35e5d7ad452",
                  "vif_model" : "avp",
                  "vif_pci_address" : "",
                  "mtu" : 9216
               }
            }
         ],
         "wrs-sg:server_group" : "",
         "OS-EXT-STS:task_state" : "",
         "wrs-res:topology" : "node:0,  4096MB, pgsize:2M, 1s,3c,1t, vcpus:0-2, pcpus:4,20,7, pol:ded, thr:pre",
         "progress" : 0,
         "wrs-res:vcpus" : [
            3,
            3,
            3
         ],
         "key_name" : "",
         "image" : {
            "id" : "7ba636ef-5dfd-4e67-ad32-cd23ee74e1eb",
            "links" : [
               {
                  "rel" : "bookmark",
                  "href" : "http://192.168.100.100:8774/ad979139d5ea4a84b21b3620c0e4761e/images/7ba636ef-5dfd-4e67-ad32-cd23ee74e1eb"
               }
            ]
         },
         "created" : "2018-03-27T02:10:26Z",
         "addresses" : {
            "mgmt" : [
               {
                  "OS-EXT-IPS:type" : "fixed",
                  "version" : 4,
                  "OS-EXT-IPS-MAC:mac_addr" : "fa:16:3e:54:f8:a6",
                  "addr" : "192.168.1.11"
               }
            ]
         },
         "os-extended-volumes:volumes_attached" : []
      },
      {
         "accessIPv4" : "",
         "OS-EXT-SRV-ATTR:instance_name" : "instance-00000008",
         "OS-SRV-USG:terminated_at" : "",
         "accessIPv6" : "",
         "config_drive" : "",
         "OS-DCF:diskConfig" : "AUTO",
         "updated" : "2018-03-27T02:12:15Z",
         "metadata" : {},
         "id" : "1b6f6671-b680-42cd-89e9-fc4ddd5d2e02",
         "flavor" : {
            "id" : "0d3b1381-1626-4f6b-869b-4a4d5d42085e",
            "links" : [
               {
                  "rel" : "bookmark",
                  "href" : "http://192.168.100.100:8774/ad979139d5ea4a84b21b3620c0e4761e/flavors/0d3b1381-1626-4f6b-869b-4a4d5d42085e"
               }
            ]
         },
         "links" : [
            {
               "rel" : "self",
               "href" : "http://192.168.100.100:8774/v2.1/ad979139d5ea4a84b21b3620c0e4761e/servers/1b6f6671-b680-42cd-89e9-fc4ddd5d2e02"
            },
            {
               "rel" : "bookmark",
               "href" : "http://192.168.100.100:8774/ad979139d5ea4a84b21b3620c0e4761e/servers/1b6f6671-b680-42cd-89e9-fc4ddd5d2e02"
            }
         ],
         "OS-EXT-SRV-ATTR:host" : "compute-0",
         "OS-EXT-AZ:availability_zone" : "nova",
         "name" : "test3",
         "wrs-res:pci_devices" : "",
         "hostId" : "b3479a460f5effda10c6fdb860e824be631026c1d09f551479180577",
         "user_id" : "777155411f3042c9b7e3194188d6f85d",
         "status" : "ACTIVE",
         "OS-EXT-STS:power_state" : 1,
         "OS-EXT-SRV-ATTR:hypervisor_hostname" : "compute-0",
         "tenant_id" : "ad979139d5ea4a84b21b3620c0e4761e",
         "OS-SRV-USG:launched_at" : "2018-03-27T02:12:15.000000",
         "OS-EXT-STS:vm_state" : "active",
         "wrs-if:nics" : [
            {
               "nic1" : {
                  "mac_address" : "fa:16:3e:4e:9b:75",
                  "network" : "mgmt",
                  "port_id" : "72d13987-1d94-4a64-aa1a-973869ae1cad",
                  "vif_model" : "avp",
                  "vif_pci_address" : "",
                  "mtu" : 9216
               }
            }
         ],
         "wrs-sg:server_group" : "",
         "OS-EXT-STS:task_state" : "",
         "wrs-res:topology" : "node:0,  4096MB, pgsize:2M, 1s,3c,1t, vcpus:0-2, pcpus:19,3,22, pol:ded, thr:pre",
         "progress" : 0,
         "wrs-res:vcpus" : [
            3,
            3,
            3
         ],
         "key_name" : "",
         "image" : {
            "id" : "7ba636ef-5dfd-4e67-ad32-cd23ee74e1eb",
            "links" : [
               {
                  "rel" : "bookmark",
                  "href" : "http://192.168.100.100:8774/ad979139d5ea4a84b21b3620c0e4761e/images/7ba636ef-5dfd-4e67-ad32-cd23ee74e1eb"
               }
            ]
         },
         "created" : "2018-03-27T02:10:01Z",
         "addresses" : {
            "mgmt" : [
               {
                  "OS-EXT-IPS:type" : "fixed",
                  "version" : 4,
                  "OS-EXT-IPS-MAC:mac_addr" : "fa:16:3e:4e:9b:75",
                  "addr" : "192.168.1.8"
               }
            ]
         },
         "os-extended-volumes:volumes_attached" : []
      }
   ]
}

SUCCESS_VMSTATE_RESPONSE = {
'result':[
    {
        'name': 'test1',
        'power_state': 3,
        'id': '12f5b1d0-fe5c-469f-a7d4-b62a91134bf8',
        'state': 'paused',
        'tenant_id': 'ad979139d5ea4a84b21b3620c0e4761e',
        'host': 'compute-0',
        'availability_zone': 'nova',
        'launched_at': '2018-03-27T02:16:40.000000'
    },
    {
        'name': 'test2',
        'power_state': 1,
        'id': '3f1b0375-a1db-4d94-b336-f32c82c0d7ec',
        'state': 'active',
        'tenant_id': 'ad979139d5ea4a84b21b3620c0e4761e',
        'host': 'compute-0',
        'availability_zone': 'nova',
        'launched_at': '2018-03-27T02:12:21.000000'
    },
    {
        'name': 'test3',
        'power_state': 1,
        'id': '1b6f6671-b680-42cd-89e9-fc4ddd5d2e02',
        'state': 'active',
        'tenant_id': 'ad979139d5ea4a84b21b3620c0e4761e',
        'host': 'compute-0',
        'availability_zone': 'nova',
        'launched_at': '2018-03-27T02:12:15.000000'
    }
    ]
}

class TestEvents(test_base.TestRequest):
    def setUp(self):
        super(TestEvents, self).setUp()

    def _get_mock_response(self, return_value=None):
        mock_response = mock.Mock(spec=test_base.MockResponse)
        mock_response.status_code = status.HTTP_200_OK
        mock_response.json.return_value = return_value
        return mock_response

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_events_check_success(self, mock_get_vim_info, mock_get_session):
        mock_get_vim_info.return_value = mock_info.MOCK_VIM_INFO
        mock_get_session.return_value = test_base.get_mock_session(
            ["get"], {
                "side_effect": [
                    self._get_mock_response(MOCK_GET_SERVERS_DETAIL_RESPONSE),
                ]
            })

        response = self.client.post(
            "/api/multicloud-ocata/v0/windriver-hudson-dc_RegionOne/events_check",
            HTTP_X_AUTH_TOKEN=mock_info.MOCK_TOKEN_ID)

        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertEqual(SUCCESS_VMSTATE_RESPONSE, response.data)
