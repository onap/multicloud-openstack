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
from newton.pub.utils.restcall import req_by_msb

logger = logging.getLogger(__name__)

def get_vims():
    retcode, content, status_code = \
        req_by_msb("/api/aai-cloudInfrastructure/v1/cloud-infrastructure/cloud-regions", "GET")
    if retcode != 0:
        logger.error("Status code is %s, detail is %s.", status_code, content)
        raise VimDriverNewtonException("Failed to query VIMs from extsys.")
    return json.JSONDecoder().decode(content)

def get_vim_by_id(vim_id):

    m = re.search(r'^([0-9a-zA-Z-]+)_([0-9a-zA-Z_-]+)$', vim_id)
    cloud_owner,cloud_region_id = m.group(1),m.group(2)

    if cloud_owner and cloud_region_id:
        retcode, content, status_code = \
            req_by_msb("/api/aai-cloudInfrastructure/v1/cloud-infrastructure/cloud-regions/cloud-region/%s/%s" % (cloud_owner,cloud_region_id), "GET")
        if retcode != 0:
            logger.error("Status code is %s, detail is %s.", status_code, content)
            raise VimDriverNewtonException(
                "Failed to query VIM with id (%s:%s,%s) from extsys." % (vim_id,cloud_owner,cloud_region_id),
                status.HTTP_404_NOT_FOUND, content)
        return json.JSONDecoder().decode(content)
    else:
        return None



