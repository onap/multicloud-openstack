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
import json
import traceback
from keystoneauth1.exceptions import HttpError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from newton.pub.exceptions import VimDriverNewtonException

from util import VimDriverUtils

logger = logging.getLogger(__name__)

DEBUG=True

class Tenants(APIView):
    service = {'service_type': 'identity',
               'interface': 'public',
               'region_name': 'RegionOne'}
    keys_mapping = [
        ("projects", "tenants"),
    ]

    def get(self, request, vimid=""):
        logger.debug("Tenants--get::> %s" % request.data)
        try:
            #prepare request resource to vim instance
            query = VimDriverUtils.get_query_part(request)

            vim = VimDriverUtils.get_vim_info(vimid)
            if '/v2' in vim["url"]:
                req_resouce = "/v2.0/tenants"
            elif '/v3' in vim["url"]:
                req_resouce = "/projects"
            else:
                req_resouce = "/projects"

            sess = VimDriverUtils.get_session(vim)
            resp = sess.get(req_resouce, endpoint_filter=self.service)
            content = resp.json()
            vim_dict = {
                "vimName": vim["name"],
                "vimId": vim["vimId"],
            }
            content.update(vim_dict)

            VimDriverUtils.replace_key_by_mapping(content,
                                                    self.keys_mapping)

            if query:
               _, tenantname = query.split('=')
               if tenantname:
                   tmp=content["tenants"]
                   content["tenants"] = []
                   # convert the key naming in hosts
                   for tenant in tmp:
                       if tenantname == tenant['name']:
                           content["tenants"].append(tenant)


            return Response(data=content, status=resp.status_code)
        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

