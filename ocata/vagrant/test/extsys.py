# Copyright (c) 2017-2018 Wind River Systems, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

import json
import logging
import re

from rest_framework import status
from common.exceptions import VimDriverNewtonException
from common.utils.restcall import req_by_msb,req_to_aai


logger = logging.getLogger(__name__)

tisr4 = {
    "createTime": "2017-04-01 02:22:27",
    "domain": "Default",
    "name": "TiS_R4",
    "password": "admin",
    "tenant": "admin",
    "type": "openstack",
    "url": "http://192.168.1.10:5000/v3",
    "userName": "admin",
    "vendor": "OpenStack",
    "version": "ocata",
    "vimId": "openstack-hudson-dc_RegionOne",
    'cloud_owner':'openstack-hudson-dc',
    'cloud_region_id':'RegionOne',
    'cloud_extra_info':'',
    'cloud_epa_caps':'{"huge_page":"true","cpu_pinning":"true",\
        "cpu_thread_policy":"true","numa_aware":"true","sriov":"true",\
        "dpdk_vswitch":"true","rdt":"false","numa_locality_pci":"true"}',
    'insecure':'True',
}

#    "vimId": "6e720f68-34b3-44f0-a6a4-755929b20393"

def mock_get_vim_by_id(method):
    def wrapper(vimid):
        return tisr4
    return wrapper

def mock_delete_vim_by_id(method):
    def wrapper(vimid):
        return status.HTTP_202_ACCEPTED
    return wrapper

#def get_vims():
#    retcode, content, status_code = \
#        req_by_msb("/api/aai-cloudInfrastructure/v1/cloud-infrastructure/cloud-regions", "GET")
#    if retcode != 0:
#        logger.error("Status code is %s, detail is %s.", status_code, content)
#        raise VimDriverNewtonException("Failed to query VIMs from extsys.")
#    return json.JSONDecoder().decode(content)

@mock_get_vim_by_id
def get_vim_by_id(vim_id):

    cloud_owner,cloud_region_id = decode_vim_id(vim_id)

    if cloud_owner and cloud_region_id:
        retcode, content, status_code = \
            req_to_aai("/cloud-infrastructure/cloud-regions/cloud-region/%s/%s"
                       % (cloud_owner,cloud_region_id),"GET")
        if retcode != 0:
            logger.error("Status code is %s, detail is %s.", status_code, content)
            raise VimDriverNewtonException(
                "Failed to query VIM with id (%s:%s,%s)." % (vim_id,cloud_owner,cloud_region_id),
                status_code, content)
        tmp_viminfo = json.JSONDecoder().decode(content)

        #assume esr-system-info-id is composed by {cloud-owner} _ {cloud-region-id}
        retcode2,content2,status_code2 = \
            req_to_aai("/cloud-infrastructure/cloud-regions/cloud-region/%s/%s"
                       + "/esr-system-info-list/esr-system-info/%s_%s" \
                       % (cloud_owner,cloud_region_id,cloud_owner,cloud_region_id),
                       "GET")
        if retcode2 != 0:
            logger.error("Status code is %s, detail is %s.", status_code, content)
            raise VimDriverNewtonException(
                "Failed to query ESR system with id (%s:%s,%s)." % (vim_id,cloud_owner,cloud_region_id),
                status_code, content)
        tmp_authinfo = json.JSONDecoder().decode(content2)

        #convert vim information

        if tmp_viminfo:
            viminfo = {}
            viminfo['vimId'] = vim_id
            viminfo['cloud_owner'] = cloud_owner
            viminfo['cloud_region_id'] = cloud_region_id
            viminfo['type'] = tmp_viminfo['cloud-type']
            viminfo['name'] = tmp_viminfo['complex-name']
            viminfo['version'] = tmp_viminfo['cloud-region-version']
            viminfo['cloud_extra_info'] = tmp_viminfo['cloud-extra-info']
            viminfo['cloud_epa_caps'] = tmp_viminfo['cloud-epa-caps']

            if tmp_authinfo:
                viminfo['userName'] = tmp_authinfo['user-name']
                viminfo['password'] = tmp_authinfo['password']
                viminfo['domain'] = tmp_authinfo['cloud-domain']
                viminfo['url'] = tmp_authinfo['service-url']
                viminfo['tenant'] = tmp_authinfo['default-tenant']
                viminfo['cacert'] = tmp_authinfo['ssl-cacert']
                viminfo['insecure'] = tmp_authinfo['ssl-insecure']
            else:
                return None

            return viminfo
        else:
            return None
    else:
        return None

@mock_delete_vim_by_id
def delete_vim_by_id(vim_id):
    cloud_owner, cloud_region_id = decode_vim_id(vim_id)
    if cloud_owner and cloud_region_id:
        retcode, content, status_code = \
            req_to_aai("/cloud-infrastructure/cloud-regions/cloud-region/%s/%s"
                       % ( cloud_owner, cloud_region_id), "DELETE")
        if retcode != 0:
            logger.error("Status code is %s, detail is %s.", status_code, content)
            raise VimDriverNewtonException(
                "Failed to delete VIM in AAI with id (%s:%s,%s)." % (vim_id,cloud_owner,cloud_region_id),
                status_code, content)
        return 0
    # return non zero if failed to decode cloud owner and region id
    return 1

def decode_vim_id(vim_id):
    m = re.search(r'^([0-9a-zA-Z-]+)_([0-9a-zA-Z_-]+)$', vim_id)
    cloud_owner, cloud_region_id = m.group(1), m.group(2)
    return cloud_owner, cloud_region_id
