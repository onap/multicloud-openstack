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

import copy
import json

from django.test import Client
import mock
from rest_framework import status
import unittest

from newton_base.util import VimDriverUtils

MOCK_VIM_INFO = {
    "createTime": "2017-04-01 02:22:27",
    "domain": "Default",
    "name": "TiS_R4",
    "password": "admin",
    "tenant": "admin",
    "type": "openstack",
    "url": "http://128.224.180.14:5000/v3",
    "userName": "admin",
    "vendor": "WindRiver",
    "version": "titanium_cloud",
    "vimId": "windriver-hudson-dc_RegionOne",
    'cloud_owner': 'windriver-hudson-dc',
    'cloud_region_id': 'RegionOne',
    'cloud_extra_info': '',
    'insecure': 'True',
}

MOCK_TOKEN_ID = "1a62b3971d774404a504c5d9a3e506e3"

MOCK_CATALOG_RESPONSE = {
    "catalog": [
        {
            "id": "99aefcc82a9246f98f8c281e61ffc754",
            "endpoints": [
                {
                    "region": "RegionOne",
                    "url": "http://128.224.180.14:9696",
                    "id": "39583c1508ad4b71b380570a745ee10a",
                    "interface": "public",
                    "region_id": "RegionOne"
                },
                {
                    "url": "http://192.168.204.2:9696",
                    "region": "RegionOne",
                    "id": "37e8d07ba24e4b8f93490c9daaba06e2",
                    "interface": "internal",
                    "region_id": "RegionOne"
                },
                {
                    "interface": "admin",
                    "id": "7eee4ca98d444b1abb00a50d4b89373f",
                    "region_id": "RegionOne",
                    "region": "RegionOne",
                    "url": "http://192.168.204.2:9696"
                }
            ],
            "name": "neutron",
            "type": "network"
        },
        {
            "endpoints": [
                {
                    "interface": "public",
                    "id": "10496738fa374295a4a88a63b81a1589",
                    "region_id": "RegionOne",
                    "url": "http://128.224.180.14:8777",
                    "region": "RegionOne"
                },
                {
                    "id": "02dcb8c0bd464c4489fa0a0c9f28571f",
                    "region_id": "RegionOne",
                    "interface": "internal",
                    "url": "http://192.168.204.2:8777",
                    "region": "RegionOne"
                },
                {
                    "region_id": "RegionOne",
                    "id": "8a73b0d3743b4e78b87614690f6e97fe",
                    "interface": "admin",
                    "url": "http://192.168.204.2:8777",
                    "region": "RegionOne"
                }
            ],
            "id": "d131054da83f4c93833799747a0f4709",
            "name": "ceilometer",
            "type": "metering"
        },
        {
            "type": "volumev2",
            "name": "cinderv2",
            "endpoints": [
                {
                    "id": "35a67ad36f0447d19c9662babf7cf609",
                    "interface": "public",
                    "region_id": "RegionOne",
                    "url": "http://128.224.180.14:8776/v2/fcca3cc49d5e42caae15459e27103efc",
                    "region": "RegionOne"
                },
                {
                    "region": "RegionOne",
                    "url": "http://192.168.204.2:8776/v2/fcca3cc49d5e42caae15459e27103efc",
                    "id": "c6ea42052268420fa2c8d351ee68c922",
                    "interface": "internal",
                    "region_id": "RegionOne"
                },
                {
                    "region_id": "RegionOne",
                    "id": "91cb24853dc3450d847b0c286a2e44ea",
                    "interface": "admin",
                    "region": "RegionOne",
                    "url": "http://192.168.204.2:8776/v2/fcca3cc49d5e42caae15459e27103efc"
                }
            ],
            "id": "40440057102440739c30be10a66bc5d1"
        },
        {
            "name": "heat",
            "type": "orchestration",
            "id": "35300cce88db4bd4bb5a72ffe3b88b00",
            "endpoints": [
                {
                    "id": "58999d7b4a94439089ecfb2aca2d7f6c",
                    "region_id": "RegionOne",
                    "interface": "public",
                    "region": "RegionOne",
                    "url": "http://128.224.180.14:8004/v1/fcca3cc49d5e42caae15459e27103efc"
                },
                {
                    "url": "http://192.168.204.2:8004/v1/fcca3cc49d5e42caae15459e27103efc",
                    "region": "RegionOne",
                    "interface": "internal",
                    "id": "1e0ee1a2aef84802b921d422372a567e",
                    "region_id": "RegionOne"
                },
                {
                    "region": "RegionOne",
                    "url": "http://192.168.204.2:8004/v1/fcca3cc49d5e42caae15459e27103efc",
                    "id": "17661bf4859741b8a43a461dedad1871",
                    "region_id": "RegionOne",
                    "interface": "admin"
                }
            ]
        },
        {
            "id": "08dc6912aea64c01925012c8a6df250a",
            "endpoints": [
                {
                    "id": "02792c4eed77486083f9b2e52d7b94b0",
                    "region_id": "RegionOne",
                    "interface": "public",
                    "region": "RegionOne",
                    "url": "http://128.224.180.14:5000/v3"
                },
                {
                    "id": "b6d5cad394b94309ae40d8de88059c5f",
                    "region_id": "RegionOne",
                    "interface": "internal",
                    "url": "http://192.168.204.2:5000/v3",
                    "region": "RegionOne"
                },
                {
                    "region": "RegionOne",
                    "url": "http://192.168.204.2:35357/v3",
                    "region_id": "RegionOne",
                    "id": "1f18e2b7c6a34493b86853b65917888e",
                    "interface": "admin"
                }
            ],
            "type": "identity",
            "name": "keystone"
        },
        {
            "name": "vim",
            "type": "nfv",
            "endpoints": [
                {
                    "url": "http://128.224.180.14:4545",
                    "region": "RegionOne",
                    "id": "b33e317345e4480ab0786e4960995ec9",
                    "interface": "public",
                    "region_id": "RegionOne"
                },
                {
                    "region": "RegionOne",
                    "url": "http://192.168.204.2:4545",
                    "interface": "internal",
                    "id": "03c85828d5bf432ab04831aa65ac9c52",
                    "region_id": "RegionOne"
                },
                {
                    "id": "067983abb061476cb53a9e23a740d98f",
                    "region_id": "RegionOne",
                    "interface": "admin",
                    "url": "http://192.168.204.2:4545",
                    "region": "RegionOne"
                }
            ],
            "id": "01636c856fc84988b38b9117eb4a8021"
        },
        {
            "name": "aodh",
            "type": "alarming",
            "id": "eb269151d0e44744a5b5449657bdc61c",
            "endpoints": [
                {
                    "id": "5bfc6c056e0244c493642eb82f6aaa11",
                    "region_id": "RegionOne",
                    "interface": "public",
                    "url": "http://128.224.180.14:8042",
                    "region": "RegionOne"
                },
                {
                    "region": "RegionOne",
                    "url": "http://192.168.204.2:8042",
                    "region_id": "RegionOne",
                    "id": "ad69c7f76dce4089a195b9221ddbfb44",
                    "interface": "internal"
                },
                {
                    "interface": "admin",
                    "id": "3e8fcdfa7bcb40b0ae33c282adfcc9ff",
                    "region_id": "RegionOne",
                    "region": "RegionOne",
                    "url": "http://192.168.204.2:8042"
                }
            ]
        },
        {
            "name": "sysinv",
            "type": "platform",
            "endpoints": [
                {
                    "region": "RegionOne",
                    "url": "http://128.224.180.14:6385/v1",
                    "interface": "public",
                    "id": "ba4ba8104590421b84672306c7e0e1f1",
                    "region_id": "RegionOne"
                },
                {
                    "region": "RegionOne",
                    "url": "http://192.168.204.2:6385/v1",
                    "interface": "internal",
                    "id": "a1cba34b163f496ab1acd6e9b51e39a2",
                    "region_id": "RegionOne"
                },
                {
                    "url": "http://192.168.204.2:6385/v1",
                    "region": "RegionOne",
                    "id": "7c171210a2c841a6a52a5713e316d6fc",
                    "interface": "admin",
                    "region_id": "RegionOne"
                }
            ],
            "id": "256bbad671f946fea543e6bd71f98875"
        },
        {
            "id": "e84665dcce814c05b4c5084964547534",
            "endpoints": [
                {
                    "url": "http://128.224.180.14:8000/v1/fcca3cc49d5e42caae15459e27103efc",
                    "region": "RegionOne",
                    "region_id": "RegionOne",
                    "id": "b2ed1a23dc6944bea129c20861e0286a",
                    "interface": "public"
                },
                {
                    "region": "RegionOne",
                    "url": "http://192.168.204.2:8000/v1/fcca3cc49d5e42caae15459e27103efc",
                    "interface": "internal",
                    "id": "c4df7c6bc15646848eff35caf6ffea8e",
                    "region_id": "RegionOne"
                },
                {
                    "region_id": "RegionOne",
                    "id": "61b3dabb761443a89ab549f437c05ab0",
                    "interface": "admin",
                    "region": "RegionOne",
                    "url": "http://192.168.204.2:8000/v1/fcca3cc49d5e42caae15459e27103efc"
                }
            ],
            "name": "heat-cfn",
            "type": "cloudformation"
        },
        {
            "id": "823024424a014981a3721229491c0b1a",
            "endpoints": [
                {
                    "region": "RegionOne",
                    "url": "http://128.224.180.14:8776/v1/fcca3cc49d5e42caae15459e27103efc",
                    "region_id": "RegionOne",
                    "id": "4a52e4e54ff440789f9a797919c4a0f2",
                    "interface": "public"
                },
                {
                    "url": "http://192.168.204.2:8776/v1/fcca3cc49d5e42caae15459e27103efc",
                    "region": "RegionOne",
                    "id": "d4f9a84476524a39844f0fce63f1022e",
                    "region_id": "RegionOne",
                    "interface": "internal"
                },
                {
                    "region": "RegionOne",
                    "url": "http://192.168.204.2:8776/v1/fcca3cc49d5e42caae15459e27103efc",
                    "interface": "admin",
                    "id": "81bf3810a8cc4697b68c6e93b5b8fe1f",
                    "region_id": "RegionOne"
                }
            ],
            "type": "volume",
            "name": "cinder"
        },
        {
            "name": "glance",
            "type": "image",
            "endpoints": [
                {
                    "id": "bd930aba961946cfb1401bada56d55e3",
                    "region_id": "RegionOne",
                    "interface": "public",
                    "region": "RegionOne",
                    "url": "http://128.224.180.14:9292"
                },
                {
                    "region": "RegionOne",
                    "url": "http://192.168.204.2:9292",
                    "id": "c11da585f0b141b99d1e18bb9a607beb",
                    "region_id": "RegionOne",
                    "interface": "internal"
                },
                {
                    "region": "RegionOne",
                    "url": "http://192.168.204.2:9292",
                    "id": "31b26c625a6a4fc7910dc5935155996e",
                    "interface": "admin",
                    "region_id": "RegionOne"
                }
            ],
            "id": "3b78cf039bc54d1bbb99ab3a4be15ef1"
        },
        {
            "id": "b8701374bf254de1beee8a2c9ecc6b33",
            "endpoints": [
                {
                    "region_id": "RegionOne",
                    "id": "f7407f330c8b4577b1d377d3fab9c2f8",
                    "interface": "public",
                    "region": "RegionOne",
                    "url": "http://128.224.180.14:15491"
                },
                {
                    "url": "http://192.168.204.2:5491",
                    "region": "RegionOne",
                    "interface": "internal",
                    "id": "0b37ce31a32f4b6fa5e1aa0d6c20680f",
                    "region_id": "RegionOne"
                },
                {
                    "region_id": "RegionOne",
                    "id": "7b87ea72adf245e1991e9e0df29b7ea9",
                    "interface": "admin",
                    "region": "RegionOne",
                    "url": "http://192.168.204.2:5491"
                }
            ],
            "type": "patching",
            "name": "patching"
        },
        {
            "id": "0ec0923a58f04ffeb6fced3bbc5c0947",
            "endpoints": [
                {
                    "url": "http://128.224.180.14:8774/v2.1/fcca3cc49d5e42caae15459e27103efc",
                    "region": "RegionOne",
                    "id": "13168b12da17451fb39630de67db168f",
                    "region_id": "RegionOne",
                    "interface": "public"
                },
                {
                    "id": "22dd6a44209f42d986b82e3aa6535f82",
                    "interface": "internal",
                    "region_id": "RegionOne",
                    "region": "RegionOne",
                    "url": "http://192.168.204.2:8774/v2.1/fcca3cc49d5e42caae15459e27103efc"
                },
                {
                    "region": "RegionOne",
                    "url": "http://192.168.204.2:8774/v2.1/fcca3cc49d5e42caae15459e27103efc",
                    "id": "552a991ae501492f841c1b6e2ff38fc5",
                    "region_id": "RegionOne",
                    "interface": "admin"
                }
            ],
            "type": "compute",
            "name": "nova"
        },
        {
            "id": "50b219650f1049b097b3f14e8c70cdf8",
            "endpoints": [
                {
                    "interface": "public",
                    "id": "5a4276cd6e4d43e883cf8640d4e13f7d",
                    "region_id": "RegionOne",
                    "region": "RegionOne",
                    "url": "http://128.224.180.14:8776/v3/fcca3cc49d5e42caae15459e27103efc"
                },
                {
                    "region": "RegionOne",
                    "url": "http://192.168.204.2:8776/v3/fcca3cc49d5e42caae15459e27103efc",
                    "region_id": "RegionOne",
                    "id": "c796df3ca5a84fc18db5b43a55283953",
                    "interface": "internal"
                },
                {
                    "region_id": "RegionOne",
                    "id": "cf55c2b34d0049ba835a2e48b9ad0e2e",
                    "interface": "admin",
                    "url": "http://192.168.204.2:8776/v3/fcca3cc49d5e42caae15459e27103efc",
                    "region": "RegionOne"
                }
            ],
            "type": "volumev3",
            "name": "cinderv3"
        }
    ]
}

MOCK_AUTH_STATE = {
    "body": {
        "token": {
            "is_domain": "false",
            "expires_at": "2017-08-27T14:19:15.000000Z",
            "issued_at": "2017-08-27T13:19:15.000000Z",
            "roles": [
                {
                    "id": "9fe2ff9ee4384b1894a90878d3e92bab",
                    "name": "_member_"
                },
                {
                    "id": "b86a7e02935844b899d3d326f83c1b1f",
                    "name": "admin"
                },
                {
                    "name": "heat_stack_owner",
                    "id": "7de502236e954c8282de32e773fc052e"
                }
            ],
            "methods": [
                "password"
            ],
            "catalog": MOCK_CATALOG_RESPONSE['catalog'],
            "project": {
                "name": "admin",
                "id": "fcca3cc49d5e42caae15459e27103efc",
                "domain": {
                    "id": "default",
                    "name": "Default"
                }
            },
            "user": {
                "name": "admin",
                "id": "9efb043c7629497a8028d7325ca1afb0",
                "domain": {
                    "id": "default",
                    "name": "Default"
                }
            },
            "audit_ids": [
                "_ZWT10DtSZKRXIvIcxun7w"
            ]
        }
    },
    "auth_token": MOCK_TOKEN_ID
}

MOCK_INTERNAL_METADATA_CATALOG = {
    "identity": {
        "proxy_prefix": "http://172.16.77.20:9003/api/multicloud-titaniumcloud/v0/windriver-hudson-dc_RegionOne/identity",
        "prefix": "http://128.224.180.14:5000",
        "suffix": "v3"
    },
    "patching": {
        "proxy_prefix": "http://172.16.77.20:9003/api/multicloud-titaniumcloud/v0/windriver-hudson-dc_RegionOne/patching",
        "suffix": "",
        "prefix": "http://128.224.180.14:15491"
    },
    "orchestration": {
        "suffix": "v1/fcca3cc49d5e42caae15459e27103efc",
        "prefix": "http://128.224.180.14:8004",
        "proxy_prefix": "http://172.16.77.20:9003/api/multicloud-titaniumcloud/v0/windriver-hudson-dc_RegionOne/orchestration"
    },
    "volume": {
        "prefix": "http://128.224.180.14:8776",
        "suffix": "v1/fcca3cc49d5e42caae15459e27103efc",
        "proxy_prefix": "http://172.16.77.20:9003/api/multicloud-titaniumcloud/v0/windriver-hudson-dc_RegionOne/volume"
    },
    "metering": {
        "suffix": "",
        "prefix": "http://128.224.180.14:8777",
        "proxy_prefix": "http://172.16.77.20:9003/api/multicloud-titaniumcloud/v0/windriver-hudson-dc_RegionOne/metering"
    },
    "volumev3": {
        "prefix": "http://128.224.180.14:8776",
        "suffix": "v3/fcca3cc49d5e42caae15459e27103efc",
        "proxy_prefix": "http://172.16.77.20:9003/api/multicloud-titaniumcloud/v0/windriver-hudson-dc_RegionOne/volumev3"
    },
    "compute": {
        "suffix": "v2.1/fcca3cc49d5e42caae15459e27103efc",
        "prefix": "http://128.224.180.14:8774",
        "proxy_prefix": "http://172.16.77.20:9003/api/multicloud-titaniumcloud/v0/windriver-hudson-dc_RegionOne/compute"
    },
    "platform": {
        "prefix": "http://128.224.180.14:6385",
        "suffix": "v1",
        "proxy_prefix": "http://172.16.77.20:9003/api/multicloud-titaniumcloud/v0/windriver-hudson-dc_RegionOne/platform"
    },
    "nfv": {
        "proxy_prefix": "http://172.16.77.20:9003/api/multicloud-titaniumcloud/v0/windriver-hudson-dc_RegionOne/nfv",
        "prefix": "http://128.224.180.14:4545",
        "suffix": ""
    },
    "volumev2": {
        "proxy_prefix": "http://172.16.77.20:9003/api/multicloud-titaniumcloud/v0/windriver-hudson-dc_RegionOne/volumev2",
        "suffix": "v2/fcca3cc49d5e42caae15459e27103efc",
        "prefix": "http://128.224.180.14:8776"
    },
    "image": {
        "suffix": "",
        "prefix": "http://128.224.180.14:9292",
        "proxy_prefix": "http://172.16.77.20:9003/api/multicloud-titaniumcloud/v0/windriver-hudson-dc_RegionOne/image"
    },
    "network": {
        "proxy_prefix": "http://172.16.77.20:9003/api/multicloud-titaniumcloud/v0/windriver-hudson-dc_RegionOne/network",
        "prefix": "http://128.224.180.14:9696",
        "suffix": ""
    },
    "alarming": {
        "suffix": "",
        "prefix": "http://128.224.180.14:8042",
        "proxy_prefix": "http://172.16.77.20:9003/api/multicloud-titaniumcloud/v0/windriver-hudson-dc_RegionOne/alarming"
    },
    "cloudformation": {
        "proxy_prefix": "http://172.16.77.20:9003/api/multicloud-titaniumcloud/v0/windriver-hudson-dc_RegionOne/cloudformation",
        "prefix": "http://128.224.180.14:8000",
        "suffix": "v1/fcca3cc49d5e42caae15459e27103efc"
    }
}

MOCK_GET_SERVERS_RESPONSE = {
    "servers": [
        {
            "links": [
                {
                    "href": "http://128.224.180.14:8774/v2.1/fcca3cc49d5e42caae15459e27103efc/servers/b2581b5c-7c56-4564-819d-fe7a2ce9c261",
                    "rel": "self"
                },
                {
                    "href": "http://128.224.180.14:8774/fcca3cc49d5e42caae15459e27103efc/servers/b2581b5c-7c56-4564-819d-fe7a2ce9c261",
                    "rel": "bookmark"
                }
            ],
            "id": "b2581b5c-7c56-4564-819d-fe7a2ce9c261",
            "name": "t1"
        },
        {
            "id": "ff7b51ca-a272-45f4-b54c-e40b8099e67d",
            "name": "t2",
            "links": [
                {
                    "rel": "self",
                    "href": "http://128.224.180.14:8774/v2.1/fcca3cc49d5e42caae15459e27103efc/servers/ff7b51ca-a272-45f4-b54c-e40b8099e67d"
                },
                {
                    "rel": "bookmark",
                    "href": "http://128.224.180.14:8774/fcca3cc49d5e42caae15459e27103efc/servers/ff7b51ca-a272-45f4-b54c-e40b8099e67d"
                }
            ]
        }
    ]
}

MOCK_POST_SERVER_REQUEST = {
    "server": {
        "accessIPv4": "1.2.3.4",
        "accessIPv6": "80fe::",
        "name": "new-server-test",
        "imageRef": "70a599e0-31e7-49b7-b260-868f441e862b",
        "flavorRef": "1",
        "availability_zone": "nova",
        "OS-DCF:diskConfig": "AUTO",
        "metadata": {
            "My Server Name": "Apache1"
        },
        "personality": [
            {
                "path": "/etc/banner.txt",
                "contents": "ICAgICAgDQoiQSBjbG91ZCBkb2VzIG5vdCBrbm93IHdoeSBp dCBtb3ZlcyBpbiBqdXN0IHN1Y2ggYSBkaXJlY3Rpb24gYW5k IGF0IHN1Y2ggYSBzcGVlZC4uLkl0IGZlZWxzIGFuIGltcHVs c2lvbi4uLnRoaXMgaXMgdGhlIHBsYWNlIHRvIGdvIG5vdy4g QnV0IHRoZSBza3kga25vd3MgdGhlIHJlYXNvbnMgYW5kIHRo ZSBwYXR0ZXJucyBiZWhpbmQgYWxsIGNsb3VkcywgYW5kIHlv dSB3aWxsIGtub3csIHRvbywgd2hlbiB5b3UgbGlmdCB5b3Vy c2VsZiBoaWdoIGVub3VnaCB0byBzZWUgYmV5b25kIGhvcml6 b25zLiINCg0KLVJpY2hhcmQgQmFjaA=="
            }
        ],
        "security_groups": [
            {
                "name": "default"
            }
        ],
        "user_data": "IyEvYmluL2Jhc2gKL2Jpbi9zdQplY2hvICJJIGFtIGluIHlvdSEiCg=="
    },
    "OS-SCH-HNT:scheduler_hints": {
        "same_host": "48e6a9f6-30af-47e0-bc04-acaed113bb4e"
    }
}

MOCK_POST_SERVER_RESPONSE = {
    "server": {
        "OS-DCF:diskConfig": "AUTO",
        "adminPass": "6NpUwoz2QDRN",
        "id": "f5dc173b-6804-445a-a6d8-c705dad5b5eb",
        "links": [
            {
                "href": "http://openstack.example.com/v2/6f70656e737461636b20342065766572/servers/f5dc173b-6804-445a-a6d8-c705dad5b5eb",
                "rel": "self"
            },
            {
                "href": "http://openstack.example.com/6f70656e737461636b20342065766572/servers/f5dc173b-6804-445a-a6d8-c705dad5b5eb",
                "rel": "bookmark"
            }
        ],
        "security_groups": [
            {
                "name": "default"
            }
        ]
    }
}

MOCK_PATCH_IMAGE_REQUEST = [
    {
        "op": "replace",
        "path": "/name",
        "value": "Fedora 17"
    },
    {
        "op": "replace",
        "path": "/tags",
        "value": [
            "fedora",
            "beefy"
        ]
    }
]

MOCK_PATCH_IMAGE_RESPONSE = {
    "checksum": "710544e7f0c828b42f51207342622d33",
    "container_format": "ovf",
    "created_at": "2016-06-29T16:13:07Z",
    "disk_format": "vhd",
    "file": "/v2/images/2b61ed2b-f800-4da0-99ff-396b742b8646/file",
    "id": "2b61ed2b-f800-4da0-99ff-396b742b8646",
    "min_disk": 20,
    "min_ram": 512,
    "name": "Fedora 17",
    "owner": "02a7fb2dd4ef434c8a628c511dcbbeb6",
    "protected": "false",
    "schema": "/v2/schemas/image",
    "self": "/v2/images/2b61ed2b-f800-4da0-99ff-396b742b8646",
    "size": 21909,
    "status": "active",
    "tags": [
        "beefy",
        "fedora"
    ],
    "updated_at": "2016-07-25T14:48:18Z",
    "virtual_size": "",
    "visibility": "private"
}


class MockResponse(object):
    status_code = 200
    content = ''

    def json(self):
        pass


class TestServiceProxy(unittest.TestCase):
    def setUp(self):
        self.client = Client()

    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_token_cache')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_get_token(self, mock_get_vim_info, mock_get_token_cache, mock_get_session):
        mock_session_specs = ["head"]
        mock_session = mock.Mock(name='mock_session', spec=mock_session_specs)
        mock_get_servers_response_obj = mock.Mock(spec=MockResponse)
        mock_get_servers_response_obj.status_code = 200
        mock_get_servers_response_obj.content = MOCK_GET_SERVERS_RESPONSE
        mock_get_servers_response_obj.json.return_value = MOCK_GET_SERVERS_RESPONSE
        mock_session.head.return_value = mock_get_servers_response_obj

        mock_get_vim_info.return_value = MOCK_VIM_INFO
        mock_get_session.return_value = mock_session
        mock_get_token_cache.return_value = (json.dumps(MOCK_AUTH_STATE), json.dumps(MOCK_INTERNAL_METADATA_CATALOG))
        response = self.client.head(
            "/api/multicloud-titaniumcloud/v0/windriver-hudson-dc_RegionOne/compute/v2.1/fcca3cc49d5e42caae15459e27103efc/servers",
            {}, HTTP_X_AUTH_TOKEN=MOCK_TOKEN_ID)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    def test_unauthorized_access(self):
        response = self.client.get(
            "/api/multicloud-titaniumcloud/v0/windriver-hudson-dc_RegionOne/compute/v2.1/fcca3cc49d5e42caae15459e27103efc/servers")
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_expired_auth_token(self, mock_get_vim_info):
        mock_get_vim_info.return_value = MOCK_VIM_INFO

        response = self.client.get(
            "/api/multicloud-titaniumcloud/v0/windriver-hudson-dc_RegionOne/compute/v2.1/fcca3cc49d5e42caae15459e27103efc/servers",
            {}, HTTP_X_AUTH_TOKEN=MOCK_TOKEN_ID)
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    @mock.patch.object(VimDriverUtils, 'get_token_cache')
    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    def test_request_without_servicetype(self, mock_get_vim_info, mock_get_token_cache):
        mock_get_vim_info.return_value = MOCK_VIM_INFO
        mock_get_token_cache.return_value = (json.dumps(MOCK_AUTH_STATE), {})
        servicetype = "compute"
        url_part1 = "/api/multicloud-titaniumcloud/v0/windriver-hudson-dc_RegionOne/"
        url_part3 = "/v2.1/fcca3cc49d5e42caae15459e27103efc/servers"
        url = (url_part1 + servicetype + url_part3)
        response = self.client.get(url, {}, HTTP_X_AUTH_TOKEN=MOCK_TOKEN_ID)
        self.assertEqual(status.HTTP_500_INTERNAL_SERVER_ERROR, response.status_code)

        metadata_catalog = copy.deepcopy(MOCK_INTERNAL_METADATA_CATALOG)
        metadata_catalog[servicetype] = None
        mock_get_token_cache.return_value = (json.dumps(MOCK_AUTH_STATE), json.dumps(metadata_catalog))

        response = self.client.get(url, {}, HTTP_X_AUTH_TOKEN=MOCK_TOKEN_ID)
        self.assertEqual(status.HTTP_500_INTERNAL_SERVER_ERROR, response.status_code)

        metadata_catalog = copy.deepcopy(MOCK_INTERNAL_METADATA_CATALOG)
        metadata_catalog[servicetype]['prefix'] = None
        metadata_catalog[servicetype]['proxy_prefix'] = None
        mock_get_token_cache.return_value = (json.dumps(MOCK_AUTH_STATE), json.dumps(metadata_catalog))

        response = self.client.get(url, {}, HTTP_X_AUTH_TOKEN=MOCK_TOKEN_ID)
        self.assertEqual(status.HTTP_500_INTERNAL_SERVER_ERROR, response.status_code)

    @mock.patch.object(VimDriverUtils, 'get_vim_info')
    @mock.patch.object(VimDriverUtils, 'get_session')
    @mock.patch.object(VimDriverUtils, 'get_auth_state')
    @mock.patch.object(VimDriverUtils, 'update_token_cache')
    @mock.patch.object(VimDriverUtils, 'get_token_cache')
    def test_crud_resources(
            self, mock_get_token_cache, mock_update_token_cache,
            mock_get_auth_state, mock_get_session, mock_get_vim_info):
        '''
        Test service proxy API: GET

        :param mock_get_token_cache:
        :param mock_update_token_cache:
        :param mock_get_auth_state:
        :param mock_get_session:
        :param mock_get_vim_info:
        :return:
        '''

        # mock VimDriverUtils APIs
        mock_session_specs = ["get", "post", "put", "patch", "delete"]

        mock_get_servers_response_obj = mock.Mock(spec=MockResponse)
        mock_get_servers_response_obj.status_code = 200
        mock_get_servers_response_obj.content = MOCK_GET_SERVERS_RESPONSE
        mock_get_servers_response_obj.json.return_value = MOCK_GET_SERVERS_RESPONSE

        mock_post_server_response_obj = mock.Mock(spec=MockResponse)
        mock_post_server_response_obj.status_code = 202
        mock_post_server_response_obj.content = MOCK_POST_SERVER_RESPONSE
        mock_post_server_response_obj.json.return_value = MOCK_POST_SERVER_RESPONSE

        mock_patch_server_response_obj = mock.Mock(spec=MockResponse)
        mock_patch_server_response_obj.status_code = 202
        mock_patch_server_response_obj.content = MOCK_PATCH_IMAGE_REQUEST
        mock_patch_server_response_obj.json.return_value = MOCK_PATCH_IMAGE_REQUEST

        mock_delete_server_response_obj = mock.Mock(spec=MockResponse)
        mock_delete_server_response_obj.status_code = 204

        mock_session = mock.Mock(name='mock_session', spec=mock_session_specs)
        mock_session.get.return_value = mock_get_servers_response_obj
        mock_session.post.return_value = mock_post_server_response_obj
        mock_session.patch.return_value = mock_patch_server_response_obj
        mock_session.delete.return_value = mock_delete_server_response_obj

        mock_get_vim_info.return_value = MOCK_VIM_INFO
        mock_get_session.return_value = mock_session
        mock_get_auth_state.return_value = json.dumps(MOCK_AUTH_STATE)
        mock_update_token_cache.return_value = MOCK_TOKEN_ID
        mock_get_token_cache.return_value = (json.dumps(MOCK_AUTH_STATE), json.dumps(MOCK_INTERNAL_METADATA_CATALOG))

        # Create resource
        response = self.client.post(
            "/api/multicloud-titaniumcloud/v0/windriver-hudson-dc_RegionOne/compute/v2.1/fcca3cc49d5e42caae15459e27103efc/servers",
            MOCK_POST_SERVER_REQUEST, HTTP_X_AUTH_TOKEN=MOCK_TOKEN_ID)

        self.assertEqual(status.HTTP_202_ACCEPTED, response.status_code)
        context = response.json()
        self.assertEqual(MOCK_TOKEN_ID, response['X-Subject-Token'])
        self.assertIsNotNone(context['server'])

        # Retrieve resource
        response = self.client.get(
            "/api/multicloud-titaniumcloud/v0/windriver-hudson-dc_RegionOne/compute/v2.1/fcca3cc49d5e42caae15459e27103efc/servers",
            {}, HTTP_X_AUTH_TOKEN=MOCK_TOKEN_ID)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        context = response.json()

        self.assertEqual(MOCK_TOKEN_ID, response['X-Subject-Token'])
        self.assertIsNotNone(context['servers'])

        # Update resource
        response = self.client.get(
            "/api/multicloud-titaniumcloud/v0/windriver-hudson-dc_RegionOne/compute/v2.1/fcca3cc49d5e42caae15459e27103efc/servers",
            {}, HTTP_X_AUTH_TOKEN=MOCK_TOKEN_ID)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        context = response.json()

        self.assertEqual(MOCK_TOKEN_ID, response['X-Subject-Token'])
        self.assertIsNotNone(context['servers'])

        # simulate client to make the request
        response = self.client.delete(
            "/api/multicloud-titaniumcloud/v0/windriver-hudson-dc_RegionOne/compute/v2.1/fcca3cc49d5e42caae15459e27103efc/servers/324dfb7d-f4a9-419a-9a19-237df04b443b",
            HTTP_X_AUTH_TOKEN=MOCK_TOKEN_ID)

        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertEqual(MOCK_TOKEN_ID, response['X-Subject-Token'])
