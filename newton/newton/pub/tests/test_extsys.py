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

import json

import mock
import six
import unittest

from newton.pub.exceptions import VimDriverNewtonException
from newton.pub.msapi import extsys
from newton.pub.utils import restcall

MOCK_VIM_INFO = {
    "cloud-type": "openstack",
    "complex-name": "complex",
    "cloud-region-version": "Regionv1",
    "cloud-extra-info": "type",
    "cloud-epa-caps": "epa"
}

MOCK_ESR_SYSTEM_INFO = {
    "user-name": "test",
    "password": "secret",
    "cloud-domain": "default",
    "service-url": "http://localhost",
    "default-tenant": "demo",
    "ssl-cacert": None,
    "ssl-insecure": None
}


def returnList(items):
    def func():
        for item in items:
            yield item
        yield mock.DEFAULT

    generator = func()

    def effect(*args, **kwargs):
        return six.next(generator)

    return effect


class TestEpaCaps(unittest.TestCase):
    cloud_onwer = "windriver-hudson-cd"
    cloud_region_id = "RegionOne"
    vim_id = cloud_onwer + "_" + cloud_region_id

    def setUp(self):
        self.req_to_aai_backup = restcall.req_to_aai

    def tearDown(self):
        restcall.req_to_aai = self.req_to_aai_backup

    def test_get_vim_by_id(self):
        values = [
            (1, "test_content", 500), # Failure first call
            (0, json.dumps(MOCK_VIM_INFO), None), (1, "test_content", 500), # Failure second call
            (0, json.dumps(MOCK_VIM_INFO), None), (0, json.dumps(MOCK_ESR_SYSTEM_INFO), None)  # Success calls
        ]

        restcall.req_to_aai = mock.Mock(side_effect=returnList(values))
        self.assertRaises(VimDriverNewtonException, extsys.get_vim_by_id, self.vim_id)
        restcall.req_to_aai.assert_called_once()

        self.assertRaises(VimDriverNewtonException, extsys.get_vim_by_id, self.vim_id)

        viminfo = extsys.get_vim_by_id(self.vim_id)
        self.assertIsNotNone(viminfo)
        self.assertEquals(self.vim_id, viminfo['vimId'])
        self.assertEquals(self.cloud_onwer, viminfo['cloud_owner'])
        self.assertEquals(self.cloud_region_id, viminfo['cloud_region_id'])
        self.assertEquals(MOCK_VIM_INFO['cloud-type'], viminfo['type'])
        self.assertEquals(MOCK_VIM_INFO['complex-name'], viminfo['name'])
        self.assertEquals(MOCK_VIM_INFO['cloud-region-version'], viminfo['version'])
        self.assertEquals(MOCK_VIM_INFO['cloud-extra-info'], viminfo['cloud_extra_info'])
        self.assertEquals(MOCK_VIM_INFO['cloud-epa-caps'], viminfo['cloud_epa_caps'])

        self.assertEquals(MOCK_ESR_SYSTEM_INFO['user-name'], viminfo['userName'])
        self.assertEquals(MOCK_ESR_SYSTEM_INFO['password'], viminfo['password'])
        self.assertEquals(MOCK_ESR_SYSTEM_INFO['cloud-domain'], viminfo['domain'])
        self.assertEquals(MOCK_ESR_SYSTEM_INFO['service-url'], viminfo['url'])
        self.assertEquals(MOCK_ESR_SYSTEM_INFO['default-tenant'], viminfo['tenant'])
        self.assertEquals(MOCK_ESR_SYSTEM_INFO['ssl-cacert'], viminfo['cacert'])
        self.assertEquals(MOCK_ESR_SYSTEM_INFO['ssl-insecure'], viminfo['insecure'])

    def test_delete_vim_by_id(self):
        values = [(1, "test_content", 500),(0, None, None)]

        restcall.req_to_aai = mock.Mock(side_effect=returnList(values))
        self.assertRaises(VimDriverNewtonException, extsys.delete_vim_by_id, self.vim_id)
        self.assertEquals(0, extsys.delete_vim_by_id(self.vim_id))

    def test_decode_vim_id_successfuly(self):
        owner, region_id = extsys.decode_vim_id(self.vim_id)
        self.assertEquals(self.cloud_onwer, owner)
        self.assertEquals(self.cloud_region_id, region_id)