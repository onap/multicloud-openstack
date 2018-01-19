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
import logging

from rest_framework import status

from newton.pub.config import config
from newton_base.proxy import services as newton_services

logger = logging.getLogger(__name__)

DEBUG=True

class Services(newton_services.Services):

    def __init__(self):
        self._logger = logger


class GetTenants(newton_services.GetTenants):
    '''
    Backward compatible API for /v2.0/tenants
    '''

    def __init__(self):
        self._logger = logger

    def get(self, request, vimid="", servicetype="identity", requri='v3/projects'):
        self._logger.debug("GetTenants--get::META> %s" % request.META)
        self._logger.debug("GetTenants--get::data> %s" % request.data)
        self._logger.debug("GetTenants--get::vimid, servicetype, requri> %s,%s,%s"
                     % (vimid, servicetype, requri))

        return super(GetTenants,self).get(request, vimid, servicetype, requri)
