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

from common.exceptions import VimDriverNewtonException
from common.utils import restcall


logger = logging.getLogger(__name__)


def get_vim_by_id(vim_id):
    cloud_owner,cloud_region_id = decode_vim_id(vim_id)

    if cloud_owner and cloud_region_id:
        # get cloud region without depth
        retcode, content, status_code = \
            restcall.req_to_aai("/cloud-infrastructure/cloud-regions/cloud-region/%s/%s"
                       % (cloud_owner,cloud_region_id),"GET")
        if retcode != 0:
            logger.error("Status code is %s, detail is %s.", status_code, content)
            raise VimDriverNewtonException(
                "Failed to query VIM with id (%s:%s,%s)." % (vim_id,cloud_owner,cloud_region_id),
                status_code, content)
        tmp_viminfo = json.JSONDecoder().decode(content)

        # get esr-system-info under this cloud region
        retcode2, content2, status_code2 = \
            restcall.req_to_aai("/cloud-infrastructure/cloud-regions/cloud-region/%s/%s/esr-system-info-list"
                       % (cloud_owner,cloud_region_id),"GET")
        if retcode2 != 0:
            logger.error("Status code is %s, detail is %s.", status_code2, content2)
            raise VimDriverNewtonException(
                "Failed to query esr info for VIM with id (%s:%s,%s)." % (vim_id,cloud_owner,cloud_region_id),
                status_code2, content2)
        tmp_authinfo = json.JSONDecoder().decode(content2)

        # get the first auth info by default
        tmp_authinfo = tmp_authinfo['esr-system-info'][0] if tmp_authinfo \
                                                             and tmp_authinfo.get('esr-system-info', None) else None

        #convert vim information
        if tmp_viminfo and tmp_authinfo:
            viminfo = {}
            viminfo['vimId'] = vim_id
            viminfo['resource-version'] = tmp_viminfo.get('resource-version')
            viminfo['cloud_owner'] = cloud_owner
            viminfo['cloud_region_id'] = cloud_region_id
            viminfo['type'] = tmp_viminfo.get('cloud-type')
            viminfo['name'] = tmp_viminfo.get('complex-name')
            viminfo['version'] = tmp_viminfo.get('cloud-region-version')
            viminfo['cloud_extra_info'] = tmp_viminfo.get('cloud-extra-info')

            viminfo['userName'] = tmp_authinfo['user-name']
            viminfo['password'] = tmp_authinfo['password']
            viminfo['domain'] = tmp_authinfo.get('cloud-domain')
            viminfo['url'] = tmp_authinfo.get('service-url')
            viminfo['tenant'] = tmp_authinfo.get('default-tenant')
            viminfo['cacert'] = tmp_authinfo.get('ssl-cacert')
            viminfo['insecure'] = tmp_authinfo.get('ssl-insecure')
            viminfo["complex-name"] = tmp_viminfo.get("complex-name")
            viminfo['openstack_region_id'] = tmp_viminfo.get("cloud-epa-caps") \
                if tmp_viminfo.get("cloud-epa-caps") else cloud_region_id

            return viminfo
    return None

def delete_vim_by_id(vim_id):
    cloud_owner, cloud_region_id = decode_vim_id(vim_id)
    if cloud_owner and cloud_region_id:
        #get the vim info
        viminfo = get_vim_by_id(vim_id)
        if not viminfo or not viminfo['resource-version']:
            return 0

        retcode, content, status_code = \
            restcall.req_to_aai("/cloud-infrastructure/cloud-regions/cloud-region/%s/%s?resource-version=%s"
                       % ( cloud_owner, cloud_region_id, viminfo['resource-version']), "DELETE")
        if retcode != 0:
            logger.error("Status code is %s, detail is %s.", status_code, content)
            raise VimDriverNewtonException(
                "Failed to delete VIM in AAI with id (%s:%s,%s)." % (vim_id,cloud_owner,cloud_region_id),
                status_code, content)
        return 0
    # return non zero if failed to decode cloud owner and region id
    return 1

def encode_vim_id(cloud_owner, cloud_region_id):
    '''
    compose vim_id by cloud_owner and cloud_region, make sure the vimid can be converted back when talking to AAI,etc.
    This is a backward compatibility design to reuse the existing implementation code
    :param cloud_owner:
    :param cloud_region:
    :return:
    '''

    # since the {cloud_owner}/{cloud_region_id"} is globally unique, the concatenated one as below will be unique as well.
    vim_id = cloud_owner + "_" + cloud_region_id

    #other options:
    #1, store it into cache so the decode and just look up the cache for decoding
    #2, use other delimiter in case '_' is used by cloud owner/cloud region id
    # , e.g. '.', '#', hence the decode need to try more than one time

    return vim_id

def decode_vim_id(vim_id):
    m = re.search(r'^([0-9a-zA-Z-]+)_([0-9a-zA-Z_-]+)$', vim_id)
    cloud_owner, cloud_region_id = m.group(1), m.group(2)
    return cloud_owner, cloud_region_id

