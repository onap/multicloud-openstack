# Copyright (c) 2017 Wind River Systems, Inc.
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
from newton.pub.exceptions import VimDriverNewtonException
from newton.pub.utils.restcall import req_by_msb,req_to_aai


logger = logging.getLogger(__name__)

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
            req_to_aai("/cloud-infrastructure/esr-system-info/%s/%s/%s_%s" \
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
                viminfo['url'] = tmp_authinfo['url']
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

