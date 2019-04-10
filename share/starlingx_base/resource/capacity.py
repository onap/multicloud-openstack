# Copyright (c) 2017-2019 Wind River Systems, Inc.
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
import traceback
import json

from django.core.cache import cache

from newton_base.resource import capacity as newton_capacity
from common.exceptions import VimDriverNewtonException
from newton_base.util import VimDriverUtils

from keystoneauth1.exceptions import HttpError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from common.msapi import extsys

logger = logging.getLogger(__name__)


class CapacityCheck(newton_capacity.CapacityCheck):
    def __init__(self):
        super(CapacityCheck, self).__init__()
        self._logger = logger

    def post(self, request, vimid=""):
        self._logger.info("vimid, data> %s, %s" % (vimid, request.data))
        self._logger.debug("META> %s" % request.META)

        try:

            # Get the specified tenant id
            specified_project_idorname = request.META.get("Project", None)
            hasEnoughResource = self.get_tenant_cap_info(vimid, request.data, specified_project_idorname)
            azCapInfo = self.get_az_cap_info(vimid)
            self._logger.info("RESP with data> result:%s" % hasEnoughResource)
            return Response(data={'result': hasEnoughResource, 'AZs': azCapInfo}, status=status.HTTP_200_OK)
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return Response(data={'result': False, 'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_az_cap_info(self, vimid):
        azCapInfo = []
        # viminfo = VimDriverUtils.get_vim_info(vimid)
        # if not viminfo:
        #     self._logger.warn("azcap_audit no valid vimid: %s" % vimid)
        #     return
        # session = VimDriverUtils.get_session(
        #     viminfo,
        #     tenant_name=viminfo.get('tenant', None)
        # )
        try:
            # get list of AZ
            vimAzCacheKey = "cap_azlist_" + vimid
            vimAzListCacheStr = cache.get(vimAzCacheKey)
            self._logger.debug("Found AZ list: %s" % vimAzListCacheStr)
            vimAzListCache = json.loads(vimAzListCacheStr) if vimAzListCacheStr else []
            azCapInfoList = []
            for azName in vimAzListCache:
                azCapCacheKey = "cap_" + vimid + "_" + azName
                azCapInfoCacheStr = cache.get(azCapCacheKey)
                self._logger.debug("Found AZ info: %s, %s" % (azCapCacheKey, azCapInfoCacheStr))
                if not azCapInfoCacheStr:
                    continue
                azCapInfoCache = json.loads(azCapInfoCacheStr) if azCapInfoCacheStr else None

                azCapInfo = {}
                azCapInfo["availability-zone-name"] = azName
                # vcpu ratio: cpu_allocation_ratio=16 by default
                azCapInfo["vCPUAvail"] = \
                    (azCapInfoCache.get("vcpus", 0)
                     - azCapInfoCache.get("vcpus_used", 0)) * 16
                azCapInfo["vCPUTotal"] = azCapInfoCache.get("vcpus", 0) * 16
                # mem size in MB
                azCapInfo["MemoryAvail"] = azCapInfoCache.get("free_ram_mb", 0) / 1024.0
                azCapInfo["MemoryTotal"] = azCapInfoCache.get("memory_mb", 0) / 1024.0
                azCapInfo["StorageAvail"] = azCapInfoCache.get("free_disk_gb", 0)
                azCapInfo["StorageTotal"] = azCapInfoCache.get("local_gb", 0)
                azCapInfoList.append(azCapInfo)

            return azCapInfoList
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return azCapInfo


class APIv1CapacityCheck(CapacityCheck):
    def __init__(self):
        super(APIv1CapacityCheck, self).__init__()
        # self._logger = logger

    def post(self, request, cloud_owner="", cloud_region_id=""):
        self._logger.info("vimid, data> %s,%s, %s" % (cloud_owner, cloud_region_id, request.data))
        self._logger.debug("META> %s" % request.META)

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1CapacityCheck, self).post(request, vimid)
