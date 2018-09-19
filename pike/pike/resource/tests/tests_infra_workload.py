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

import unittest
import json
from rest_framework import status

from common.utils import restcall
from common.msapi.helper import Helper as helper
from pike.resource.views.infra_workload import InfraWorkload
from pike.resource.views.infra_workload import APIv1InfraWorkload

MOCK_TOKEN_RESPONSE = {"access":
                           {"token":
                                {"issued_at":"2018-05-10T16:56:56.000000Z",
                                 "expires":"2018-05-10T17:56:56.000000Z",
                                 "id":"4a832860dd744306b3f66452933f939e",
                                 "tenant":{"domain":{"id":"default","name":"Default"},
                                           "enabled":"true","id":"0e148b76ee8c42f78d37013bf6b7b1ae",
                                           "name":"VIM"}},"serviceCatalog":[],
                            "user":{"domain":{"id":"default","name":"Default"},
                                    "id":"ba76c94eb5e94bb7bec6980e5507aae2",
                                    "name":"demo"}}}

MOCK_HEAT_CREATE_BODY1 =   {
     "generic-vnf-id":"MOCK_GENERIF_VNF_ID1",
     "vf-module-id":"MOCK_VF_MODULE_ID1",
     "oof_directives":{
         "directives":[
             {
                 "id":"MOCK_VNFC_ID1",
                 "type": "vnfc",
                 "directives":[{
                     "type":"flavor_directives",
                     "attributes":[
                         {
                             "attribute_name":"flavor1",
                             "attribute_value":"m1.hpa.medium"
                         }
                     ]
                 }
                 ]
             }
         ]
     },
     "sdnc_directives":{},
     "template_type":"HEAT",
     "template_data":{
         "files":{  },
         "disable_rollback":True,
         "parameters":{
             "flavor1":"m1.heat"
         },
         "stack_name":"teststack",
         "template":{
             "heat_template_version":"2013-05-23",
             "description":"Simple template to test heat commands",
             "parameters":
                 {
                     "flavor":{
                         "default":"m1.tiny",
                         "type":"string"
                     }
                 },
             "resources":{
                 "hello_world":{
                     "type":"OS::Nova::Server",
                     "properties":{
                         "key_name":"heat_key",
                         "flavor":{
                             "get_param":"flavor"
                         },
                         "image":"40be8d1a-3eb9-40de-8abd-43237517384f",
                         "user_data":"#!/bin/bash -xv\necho \"hello world\" &gt; /root/hello-world.txt\n"
                     }
                 }
             }
         },
         "timeout_mins":60
     }
}

MOCK_HEAT_CREATE_RESPONSE1 = {
    'stack': {
        'id': "MOCKED_HEAT_STACK_ID1"
    }
}

MOCK_HEAT_LIST_RESPONSE1 = {
    'stacks': [
        {
            'resource_status':"CREATE_IN_PROCESS"
        }
    ]
}

class InfraWorkloadTest(unittest.TestCase):
    def setUp(self):
        self._InfraWorkload = InfraWorkload()
        pass

    def tearDown(self):
        pass

    @mock.patch.object(helper, 'MultiCloudServiceHelper')
    @mock.patch.object(helper, 'MultiCloudIdentityHelper')
    def test_post(self,  mock_MultiCloudIdentityHelper, mock_MultiCloudServiceHelper):
        mock_request = mock.Mock()
        mock_request.META = {"testkey": "testvalue"}
        mock_request.data = MOCK_HEAT_CREATE_BODY1

        mock_MultiCloudIdentityHelper.side_effect= [
            (0, MOCK_TOKEN_RESPONSE, status.HTTP_201_CREATED)
                ]

        mock_MultiCloudServiceHelper.side_effect= [
            (0, MOCK_HEAT_CREATE_RESPONSE1, status.HTTP_201_CREATED)
                ]

        vimid = "CloudOwner_Region1"

        response = self._InfraWorkload.post(mock_request, vimid)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        pass


    @mock.patch.object(helper, 'MultiCloudServiceHelper')
    @mock.patch.object(helper, 'MultiCloudIdentityHelper')
    def test_get(self,  mock_MultiCloudIdentityHelper, mock_MultiCloudServiceHelper):
        mock_request = mock.Mock()
        mock_request.META = {"testkey": "testvalue"}

        mock_MultiCloudIdentityHelper.side_effect= [
            (0, MOCK_TOKEN_RESPONSE, status.HTTP_201_CREATED)
                ]

        mock_MultiCloudServiceHelper.side_effect= [
            (0, MOCK_HEAT_LIST_RESPONSE1, status.HTTP_200_OK)
                ]

        vimid = "CloudOwner_Region1"
        mock_stack_id = "MOCKED_HEAT_STACK_ID1"

        response = self._InfraWorkload.get(mock_request, vimid, mock_stack_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pass


class APIv1InfraWorkloadTest(unittest.TestCase):
    def setUp(self):
        self._APIv1InfraWorkload = APIv1InfraWorkload()
        pass

    def tearDown(self):
        pass

    @mock.patch.object(helper, 'MultiCloudServiceHelper')
    @mock.patch.object(helper, 'MultiCloudIdentityHelper')
    def test_post(self,  mock_MultiCloudIdentityHelper, mock_MultiCloudServiceHelper):
        mock_request = mock.Mock()
        mock_request.META = {"testkey": "testvalue"}
        mock_request.data = MOCK_HEAT_CREATE_BODY1

        mock_MultiCloudIdentityHelper.side_effect= [
            (0, MOCK_TOKEN_RESPONSE, status.HTTP_201_CREATED)
                ]

        mock_MultiCloudServiceHelper.side_effect= [
            (0, MOCK_HEAT_CREATE_RESPONSE1, status.HTTP_201_CREATED)
                ]

        cloud_owner = "CloudOwner"
        cloud_region_id = "Region1"

        response = self._APIv1InfraWorkload.post(mock_request, cloud_owner, cloud_region_id)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        pass


    @mock.patch.object(helper, 'MultiCloudServiceHelper')
    @mock.patch.object(helper, 'MultiCloudIdentityHelper')
    def test_get(self,  mock_MultiCloudIdentityHelper, mock_MultiCloudServiceHelper):
        mock_request = mock.Mock()
        mock_request.META = {"testkey": "testvalue"}

        mock_MultiCloudIdentityHelper.side_effect= [
            (0, MOCK_TOKEN_RESPONSE, status.HTTP_201_CREATED)
                ]

        mock_MultiCloudServiceHelper.side_effect= [
            (0, MOCK_HEAT_LIST_RESPONSE1, status.HTTP_200_OK)
                ]


        cloud_owner = "CloudOwner"
        cloud_region_id = "Region1"
        mock_stack_id = "MOCKED_HEAT_STACK_ID1"

        response = self._APIv1InfraWorkload.get(mock_request, cloud_owner, cloud_region_id, mock_stack_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pass
