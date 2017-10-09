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

from newton.pub.exceptions import VimDriverNewtonException
from newton.pub.utils import restcall


logger = logging.getLogger(__name__)

def get_vim_by_id(vim_id):

    cloud_owner,cloud_region_id = decode_vim_id(vim_id)

    if cloud_owner and cloud_region_id:
        retcode, content, status_code = \
            restcall.req_to_aai("/cloud-infrastructure/cloud-regions/cloud-region/%s/%s?depth=1"
                       % (cloud_owner,cloud_region_id),"GET")
        if retcode != 0:
            logger.error("Status code is %s, detail is %s.", status_code, content)
            raise VimDriverNewtonException(
                "Failed to query VIM with id (%s:%s,%s)." % (vim_id,cloud_owner,cloud_region_id),
                status_code, content)
        tmp_viminfo = json.JSONDecoder().decode(content)

        #assume esr-system-info-id is composed by {cloud-owner} _ {cloud-region-id}
#        retcode2,content2,status_code2 = \
#            restcall.req_to_aai(("/cloud-infrastructure/cloud-regions/cloud-region/%(owner)s/%(region)s"
#                                 "/esr-system-info-list/esr-system-info/%(owner)s_%(region)s" % {
#                "owner": cloud_owner, "region": cloud_region_id}), "GET")
#        if retcode2 != 0:
#            logger.error("Status code is %s, detail is %s.", status_code, content)
#            raise VimDriverNewtonException(
#                "Failed to query ESR system with id (%s:%s,%s)." % (vim_id,cloud_owner,cloud_region_id),
#                status_code2, content2)
#        tmp_authinfo = json.JSONDecoder().decode(content2)
        tmp_authinfo = tmp_viminfo['esr-system-info-list']['esr-system-info'][0] if tmp_viminfo else None

        #convert vim information
        if tmp_viminfo and tmp_authinfo:
            viminfo = {}
            viminfo['vimId'] = vim_id
            viminfo['cloud_owner'] = cloud_owner
            viminfo['cloud_region_id'] = cloud_region_id
            viminfo['type'] = tmp_viminfo.get('cloud-type')
            viminfo['name'] = tmp_viminfo.get('complex-name')
            viminfo['version'] = tmp_viminfo.get('cloud-region-version')
            viminfo['cloud_extra_info'] = tmp_viminfo.get('cloud-extra-info')
            viminfo['cloud_epa_caps'] = tmp_viminfo.get('cloud-epa-caps')

            viminfo['userName'] = tmp_authinfo['user-name']
            viminfo['password'] = tmp_authinfo['password']
            viminfo['domain'] = tmp_authinfo.get('cloud-domain')
            viminfo['url'] = tmp_authinfo.get('service-url')
            viminfo['tenant'] = tmp_authinfo.get('default-tenant')
            viminfo['cacert'] = tmp_authinfo.get('ssl-cacert')
            viminfo['insecure'] = tmp_authinfo.get('ssl-insecure')

            return viminfo
    return None

def delete_vim_by_id(vim_id):
    cloud_owner, cloud_region_id = decode_vim_id(vim_id)
    if cloud_owner and cloud_region_id:
        retcode, content, status_code = \
            restcall.req_to_aai("/cloud-infrastructure/cloud-regions/cloud-region/%s/%s"
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

