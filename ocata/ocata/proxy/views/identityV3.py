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

from django.conf import settings
from newton_base.proxy import identityV3 as newton_identityV3

logger = logging.getLogger(__name__)

# DEBUG=True

class Tokens(newton_identityV3.Tokens):

    def __init__(self):
        self.proxy_prefix = settings.MULTICLOUD_PREFIX
        self._logger = logger

class TokensV2(newton_identityV3.TokensV2):

    def __init__(self):
        self.proxy_prefix = settings.MULTICLOUD_PREFIX
        self._logger = logger

class APIv1Tokens(Tokens):
    def __init__(self):
        super(APIv1Tokens, self).__init__()
        self.proxy_prefix = settings.MULTICLOUD_API_V1_PREFIX


    def get(self, request, cloud_owner="", cloud_region_id=""):
        self._logger.info("cloud_owner,cloud_region_id: %s,%s" % (cloud_owner,cloud_region_id))
        #self._logger.debug("META> %s" % request.META)
        #self._logger.debug("data> %s" % request.data)

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1Tokens, self).get(request, vimid)


    def post(self, request, cloud_owner="", cloud_region_id=""):
        self._logger.info("cloud_owner,cloud_region_id: %s,%s" % (cloud_owner,cloud_region_id))
        #self._logger.debug("META> %s" % request.META)
        #self._logger.debug("data> %s" % request.data)

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1Tokens,self).post(request, vimid)


class APIv1TokensV2(TokensV2):
    def __init__(self):
        super(APIv1TokensV2, self).__init__()
        self.proxy_prefix = settings.MULTICLOUD_API_V1_PREFIX


    def get(self, request, cloud_owner="", cloud_region_id=""):
        self._logger.info("cloud_owner,cloud_region_id: %s,%s" % (cloud_owner,cloud_region_id))
        #self._logger.debug("META> %s" % request.META)
        #self._logger.debug("data> %s" % request.data)

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1TokensV2, self).get(request, vimid)


    def post(self, request, cloud_owner="", cloud_region_id=""):
        self._logger.info("cloud_owner,cloud_region_id: %s,%s" % (cloud_owner,cloud_region_id))
        #self._logger.debug("META> %s" % request.META)
        #self._logger.debug("data> %s" % request.data)

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1TokensV2,self).post(request, vimid)

