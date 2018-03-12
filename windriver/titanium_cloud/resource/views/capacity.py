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
import json
import traceback

from rest_framework import status

from django.conf import settings
from common.exceptions import VimDriverNewtonException
from newton_base.util import VimDriverUtils

from keystoneauth1.exceptions import HttpError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from common.msapi import extsys


logger = logging.getLogger(__name__)


class CapacityCheck(APIView):

    def __init__(self):
        self._logger = logger

    def post(self, request, vimid=""):
        self._logger.info("CapacityCheck--post::vimid, data> %s, %s" % (vimid, request.data))
        self._logger.debug("CapacityCheck--post::META> %s" % request.META)

        hasEnoughResource = False
        try :
            resource_demand = json.load(request.data)

            #get token:
            cloud_owner, regionid = extsys.decode_vim_id(vimid)
            interface = 'public'
            service = {'service_type': 'compute',
                       'interface': interface,
                       'region_id': regionid}

            tenant_name = None
            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenant_name)

            #get limit for this tenant
            req_resouce = "/limits"
            resp = sess.get(req_resouce, endpoint_filter=service)
            content = resp.json()
            compute_limits = content['limits']['absolute']

            #get total resource of this cloud region
            req_resouce = "/os-hypervisors/statistics"
            resp = sess.get(req_resouce, endpoint_filter=service)
            content = resp.json()
            hypervisor_statistics = content['hypervisor_statistics']

            #get storage limit for this tenant
            service['service_type'] = 'volumev2'
            req_resouce = "/limits"
            resp = sess.get(req_resouce, endpoint_filter=service)
            content = resp.json()
            storage_limits = content['limits']['absolute']

            # compute actual available resource for this tenant
            remainVCPU = compute_limits['maxTotalCores'] - compute_limits['totalCoresUsed']

            if (compute_limits['maxTotalCores'] > hypervisor_statistics['vcpus']):
                if hypervisor_statistics['vcpus'] > compute_limits['totalCoresUsed']:
                    remainVCPU = hypervisor_statistics['vcpus'] - compute_limits['totalCoresUsed']
                else:
                    remainVCPU = 0

            remainMEM = compute_limits['maxTotalRAMSize'] - compute_limits['totalRAMUsed']
            if hypervisor_statistics['free_ram_mb'] > remainMEM:
                remainMEM = hypervisor_statistics['free_ram_mb']

            remainStorage = storage_limits['maxTotalVolumeGigabytes'] - storage_limits['totalGigabytesUsed']
            if (remainStorage < hypervisor_statistics['free_disk_gb']):
                remainStorage = hypervisor_statistics['free_disk_gb']

            # compare resource demanded with available
            if (resource_demand['vCPU'] >= remainVCPU):
                hasEnoughResource = False
            elif (resource_demand['Memory'] >= remainMEM):
                hasEnoughResource = False
            elif (resource_demand['Storage'] >= remainStorage):
                hasEnoughResource = False
            else:
                hasEnoughResource = True

            return Response(data={'result': hasEnoughResource}, status=status.HTTP_200_OK)
        except VimDriverNewtonException as e:
            return Response(data={'result': hasEnoughResource,'error': e.content}, status=e.status_code)
        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            resp = e.response.json()
            resp.update({'result': hasEnoughResource})
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return Response(data={'result': hasEnoughResource, 'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

