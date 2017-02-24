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
from json import JSONEncoder

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from newton.pub.utils.restcall import req_to_vim
from newton.pub.exceptions import VimDriverNewtonException
from newton.pub.msapi.extsys import get_vim_by_id

logger = logging.getLogger(__name__)


class VimDriverUtils(object):
    @staticmethod
    def get_vim_info(vimid):
        # get vim info from local cache firstly
        # if cache miss, get it from ESR service
        vim = get_vim_by_id(vimid)
        return vim

    @staticmethod
    def relay_request_to_vim_service(vimid, tenantid, request, service_type,
                                     req_resouce, req_content=""):
        """
        if there is no token cache, do auth
        if there is, use token directly
        if response is 'need auth', do auth
        get the use extractor to get token
        and service rul and then do request
        """
        vim = VimDriverUtils.get_vim_info(vimid)
        auth_resouce = "/tokens"
        method = "POST"
        headers = ""
        r_content_dict = {
            "auth": {
                "tenantName": vim["tenant"],
                "passwordCredentials": {
                    "username": vim["userName"],
                    "password": vim["password"]
                }
            }
        }
        r_content = JSONEncoder().encode(r_content_dict)
        retcode, content, status_code = \
            req_to_vim(vim["url"], auth_resouce, method, headers, r_content)
        if retcode != 0:
            logger.error("Status code is %s, detail is %s.",
                         status_code, content)
            raise VimDriverNewtonException("Fail to authorize",
                                           status_code, content)
        else:
            # extract token id and issue the get request
            json_content = None
            auth_resp = json.JSONDecoder().decode(content)
            tokenid, svcurl = VimDriverUtils.extractor(auth_resp, service_type)
            method = request.method
            headers = {'X-Auth-Token': tokenid}
            retcode, content, status_code = \
                req_to_vim(svcurl, req_resouce, method, headers, req_content)
            if retcode != 0:
                logger.error("Status code is %s, detail is %s.",
                             status_code, content)
                raise VimDriverNewtonException("Fail to complte request",
                                               status_code, content)
            else:
                json_content = json.JSONDecoder().decode(content)
                vim_dict = {
                    "vimName": vim["name"],
                    "vimId": vim["vimId"],
                    "tenantId": tenantid,
                }
                json_content.update(vim_dict)
            return status_code, json_content

    @staticmethod
    def extractor(resp_data, service_type):
        try:
            tokenid = resp_data["access"]["token"]["id"]
            sc = resp_data["access"]["serviceCatalog"]
            service = [svc for svc in sc if svc["type"] == service_type]
            return tokenid, service[0]["endpoints"][0]["publicURL"]
        except Exception:
            raise Exception(
                "There is no valid %s token or service info" % service_type)


class Networks(APIView):
    SERVICE = "network"
    keys_map_resp = [
        ("provider:segmentation_id", "segmentationId"),
        ("provider:physical_network", "physicalNetwork"),
        ("router:external", "routerExternal"),
        ("provider:network_type", "networkType"),
        ("vlan_transparent", "vlanTransparent"),
    ]

    def get(self, request, vimid="", tenantid="", networkid=""):
        logger.debug("Networks--get::> %s" % request.data)
        try:
            # prepare request resource to vim instance
            req_resouce = "v2.0/networks"
            full_path = request.get_full_path()
            if '?' in full_path:
                _, query = request.get_full_path().split('?')
                req_resouce += "?%s" % query
            status_code, content = VimDriverUtils.relay_request_to_vim_service(
                vimid, tenantid, request, self.SERVICE, req_resouce)

            logger.debug("response content after11: %s" % content)
            # convert the key naming in networks
            for network in content["networks"]:
                for k in self.keys_map_resp:
                    v = network.pop(k[0], None)
                    if v:
                        network[k[1]] = v
            logger.debug("response content after: %s" % content)
            return Response(data=content, status=status_code)
        except VimDriverNewtonException as e:
            return Response(data=e.content, status=e.status_code)
        except Exception as e:
            return Response(data={'error': e},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, tenantid=""):
        logger.debug("Networks--post::> %s" % request.data)
        pass

    def delete(self, request):
        logger.debug("Networks--delete::> %s" % request.data)
        pass


class Subnets(APIView):
    pass
