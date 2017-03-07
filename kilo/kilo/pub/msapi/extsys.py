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

from rest_framework import status
from kilo.pub.exceptions import VimDriverKiloException
from kilo.pub.utils.restcall import req_by_msb

logger = logging.getLogger(__name__)


def get_vims():
    retcode, content, status_code = \
        req_by_msb("/openoapi/extsys/v1/vims", "GET")
    if retcode != 0:
        logger.error("Status code is %s, detail is %s.", status_code, content)
        raise VimDriverKiloException("Failed to query VIMs from extsys.")
    return json.JSONDecoder().decode(content)


def get_vim_by_id(vim_id):
    retcode, content, status_code = \
        req_by_msb("/openoapi/extsys/v1/vims/%s" % vim_id, "GET")
    if retcode != 0:
        logger.error("Status code is %s, detail is %s.", status_code, content)
        raise VimDriverKiloException(
            "Failed to query VIM with id (%s) from extsys." % vim_id,
            status.HTTP_404_NOT_FOUND, content)
    return json.JSONDecoder().decode(content)
