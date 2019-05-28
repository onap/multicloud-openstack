# Copyright (c) 2017 Wind River Systems, Inc.
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

from keystoneauth1.exceptions import HttpError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import VimDriverNewtonException
from newton_base.util import VimDriverUtils
from common.msapi import extsys

logger = logging.getLogger(__name__)


class Tenants(APIView):
    service = {
        'service_type': 'identity',
        'interface': 'public'
    }

    keys_mapping = [
        ("projects", "tenants"),
    ]

    def __init__(self):
        super(Tenants, self).__init__()
        self._logger = logger

    def get(self, request, vimid=""):
        self._logger.info("vimid = %s" % vimid)
        if request.data:
            self._logger.debug("With data = %s" % request.data)
            pass
        try:
            #prepare request resource to vim instance
            query = VimDriverUtils.get_query_part(request)

            vim = VimDriverUtils.get_vim_info(vimid)
            req_resouce = "/projects"
            if '/v2.0' in vim["url"]:
                req_resouce = "/tenants"

            sess = VimDriverUtils.get_session(vim)

            self.service['region_name'] = vim['openstack_region_id'] \
                if vim.get('openstack_region_id') \
                else vim['cloud_region_id']

            self._logger.info("making request with URI:%s" % req_resouce)
            resp = sess.get(req_resouce, endpoint_filter=self.service)
            self._logger.info("request returns with status %s" % resp.status_code)
            if resp.status_code == status.HTTP_200_OK:
                self._logger.debug("with content:%s" % resp.json())
                pass

            content = resp.json()
            vim_dict = {
                "vimName": vim["name"],
                "vimId": vim["vimId"],
                "cloud-owner": vim["cloud_owner"],
                "cloud-region-id": vim["cloud_region_id"],
            }
            content.update(vim_dict)

            VimDriverUtils.replace_key_by_mapping(
                content, self.keys_mapping)

            if query:
               _, tenantname = query.split('=')
               if tenantname:
                   tmp = content["tenants"]
                   content["tenants"] = []
                   # convert the key naming in hosts
                   for tenant in tmp:
                       if tenantname == tenant['name']:
                           content["tenants"].append(tenant)
            self._logger.info("response with status = %s" % resp.status_code)
            return Response(data=content, status=resp.status_code)
        except VimDriverNewtonException as e:
            self._logger.error("response with status = %s" % e.status_code)
            return Response(
                data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s" % (
                e.http_status, e.response.json()))
            return Response(data=e.response.json(),
                            status=e.http_status)
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return Response(
                data={'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class APIv1Tenants(Tenants):

    def __init__(self):
        super(APIv1Tenants, self).__init__()
        self._logger = logger

    def get(self, request, cloud_owner="", cloud_region_id=""):
        self._logger.info("registration with : %s, %s" % (cloud_owner, cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1Tenants, self).get(request, vimid)

