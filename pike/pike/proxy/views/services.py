# Copyright (c) 2018 Intel Corporation.
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

from django.conf import settings
from newton_base.proxy import services as newton_services
from common.msapi import extsys

logger = logging.getLogger(__name__)

# DEBUG=True

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

class APIv1Services(Services):

    def __init__(self):
        super(APIv1Services, self).__init__()
        # self._logger = logger

    def head(self, request, cloud_owner="", cloud_region_id="", servicetype="", requri=""):
        self._logger.info("cloud_owner,cloud_region_id: %s,%s" % (cloud_owner, cloud_region_id))
        # self._logger.info("servicetype, requri> %s,%s" % (servicetype, requri))
        # self._logger.debug("META, data> %s , %s" % (request.META, request.data))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1Services,self).head(request, vimid, servicetype, requri)

    def get(self, request, cloud_owner="", cloud_region_id="", servicetype="", requri=""):
        self._logger.info("cloud_owner,cloud_region_id: %s,%s" % (cloud_owner, cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1Services,self).get(request, vimid, servicetype, requri)

    def post(self, request, cloud_owner="", cloud_region_id="", servicetype="", requri=""):
        self._logger.info("cloud_owner,cloud_region_id: %s,%s" % (cloud_owner, cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1Services,self).post(request, vimid, servicetype, requri)

    def put(self, request, cloud_owner="", cloud_region_id="", servicetype="", requri=""):
        self._logger.info("cloud_owner,cloud_region_id: %s,%s" % (cloud_owner, cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1Services,self).put(request, vimid, servicetype, requri)

    def patch(self, request, cloud_owner="", cloud_region_id="", servicetype="", requri=""):
        self._logger.info("cloud_owner,cloud_region_id: %s,%s" % (cloud_owner, cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1Services,self).patch(request, vimid, servicetype, requri)

    def delete(self, request, cloud_owner="", cloud_region_id="", servicetype="", requri=""):
        self._logger.info("cloud_owner,cloud_region_id: %s,%s" % (cloud_owner, cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1Services,self).delete(request, vimid, servicetype, requri)


class APIv1GetTenants(GetTenants):
    '''
    Backward compatible API for /v2.0/tenants
    '''

    def __init__(self):
        super(APIv1GetTenants, self).__init__()
        # self._logger = logger

    def head(self, request, cloud_owner="", cloud_region_id="", servicetype="identity", requri=""):
        self._logger.info("cloud_owner,cloud_region_id: %s,%s" % (cloud_owner, cloud_region_id))
        # self._logger.info("servicetype, requri> %s,%s" % (servicetype, requri))
        # self._logger.debug("META, data> %s , %s" % (request.META, request.data))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1GetTenants,self).head(request, vimid, servicetype, requri)

    def get(self, request, cloud_owner="", cloud_region_id="", servicetype="identity", requri='v3/projects'):
        self._logger.info("cloud_owner,cloud_region_id: %s,%s" % (cloud_owner, cloud_region_id))
        #        self._logger.debug("with servicetype, requri> %s,%s" % (servicetype, requri))
        #        self._logger.debug("with META> %s" % request.META)

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1GetTenants,self).get(request, vimid, servicetype, requri)

    def post(self, request, cloud_owner="", cloud_region_id="", servicetype="identity", requri=""):
        self._logger.info("cloud_owner,cloud_region_id: %s,%s" % (cloud_owner, cloud_region_id))
        #        self._logger.debug("with servicetype, requri> %s,%s" % (servicetype, requri))
        #        self._logger.debug("with META> %s" % request.META)
        #        self._logger.debug("with data> %s" % request.data)

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1GetTenants,self).post(request, vimid, servicetype, requri)

    def put(self, request, cloud_owner="", cloud_region_id="", servicetype="identity", requri=""):
        self._logger.info("cloud_owner,cloud_region_id: %s,%s" % (cloud_owner, cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1GetTenants,self).put(request, vimid, servicetype, requri)

    def patch(self, request, cloud_owner="", cloud_region_id="", servicetype="identity", requri=""):
        self._logger.info("cloud_owner,cloud_region_id: %s,%s" % (cloud_owner, cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1GetTenants,self).patch(request, vimid, servicetype, requri)

    def delete(self, request, cloud_owner="", cloud_region_id="", servicetype="identity", requri=""):
        self._logger.info("cloud_owner,cloud_region_id: %s,%s" % (cloud_owner, cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1GetTenants,self).delete(request, vimid, servicetype, requri)
