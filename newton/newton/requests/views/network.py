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

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from newton.pub.exceptions import VimDriverNewtonException

from util import VimDriverUtils

logger = logging.getLogger(__name__)


class Networks(APIView):
    service = {'service_type': 'network',
               'interface': 'public',
               'region_name': 'RegionOne'}
    keys_mapping = [
        ("provider:segmentation_id", "segmentationId"),
        ("provider:physical_network", "physicalNetwork"),
        ("router:external", "routerExternal"),
        ("provider:network_type", "networkType"),
        ("vlan_transparent", "vlanTransparent"),
        ("project_id", "tenantId"),
    ]

    def get(self, request, vimid="", tenantid="", networkid=""):
        logger.debug("Networks--get::> %s" % request.data)
        try:
            content, status_code = self.get_networks(request, vimid, tenantid, networkid)
            return Response(data=content, status=status_code)

        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except Exception as e:
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_networks(self, request, vimid="", tenantid="", networkid=""):
        logger.debug("Networks--get_networks::> %s" % networkid)

        # prepare request resource to vim instance
        req_resouce = "v2.0/networks"
        if networkid:
            req_resouce += "/%s" % networkid
        query = VimDriverUtils.get_query_part(request)
        if query:
            req_resouce += "?%s" % query

        vim = VimDriverUtils.get_vim_info(vimid)
        sess = VimDriverUtils.get_session(vim, tenantid)
        resp = sess.get(req_resouce, endpoint_filter=self.service)
        content = resp.json()
        vim_dict = {
            "vimName": vim["name"],
            "vimId": vim["vimId"],
            "tenantId": tenantid,
        }
        content.update(vim_dict)

        if not networkid:
            # convert the key naming in networks
            for network in content["networks"]:
                VimDriverUtils.replace_key_by_mapping(network,
                                                      self.keys_mapping)
        else:
            # convert the key naming in the network specified by id
            network = content.pop("network", None)
            VimDriverUtils.replace_key_by_mapping(network,
                                                  self.keys_mapping)
            content.update(network)

        return content, resp.status_code

    def post(self, request, vimid="", tenantid="", networkid=""):
        logger.debug("Networks--post::> %s" % request.data)
        try:
            #check if created already: check name
            content, status_code = self.get_networks(request, vimid, tenantid)
            existed = False
            if status_code == 200:
                for network in content["networks"]:
                    if network["name"] == request.data["name"]:
                        existed = True
                        break
                    pass
                if existed == True:
                    vim_dict = {
                        "returnCode": 0,
                    }
                    network.update(vim_dict)
                    return Response(data=network, status=status_code)

            # prepare request resource to vim instance
            req_resouce = "v2.0/networks"
            if networkid:
                req_resouce += "/%s" % networkid
            query = VimDriverUtils.get_query_part(request)
            if query:
                req_resouce += "?%s" % query

            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid)
            network = request.data
            VimDriverUtils.replace_key_by_mapping(network,
                                                  self.keys_mapping, True)
            req_body = json.JSONEncoder().encode({"network": network})
            resp = sess.post(req_resouce, data=req_body,
                             endpoint_filter=self.service)
            resp_body = resp.json()["network"]
            VimDriverUtils.replace_key_by_mapping(resp_body, self.keys_mapping)
            vim_dict = {
                "vimName": vim["name"],
                "vimId": vim["vimId"],
                "tenantId": tenantid,
                "returnCode": 1,
            }
            resp_body.update(vim_dict)
            return Response(data=resp_body, status=resp.status_code)
        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except Exception as e:
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        pass

    def delete(self, request, vimid="", tenantid="", networkid=""):
        logger.debug("Networks--delete::> %s" % request.data)
        try:
            # prepare request resource to vim instance
            req_resouce = "v2.0/networks"
            if networkid:
                req_resouce += "/%s" % networkid
            query = VimDriverUtils.get_query_part(request)
            if query:
                req_resouce += "?%s" % query

            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid)
            resp = sess.delete(req_resouce, endpoint_filter=self.service)
            return Response(status=resp.status_code)
        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except Exception as e:
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        pass


class Subnets(APIView):
    pass
