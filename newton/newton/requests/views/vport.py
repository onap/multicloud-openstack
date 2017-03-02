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


class Vports(APIView):
    service = {'service_type': 'network',
               'interface': 'public',
               'region_name': 'RegionOne'}
    keys_mapping = [
        ("project_id", "tenantId"),
        ("network_id", "networkId"),
        ("binding:vnic_type", "vnicType"),
        ("security_groups", "securityGroups"),
        ("mac_address", "macAddress"),
        ("subnet_id", "subnetId"),
        ("ip_address", "ip"),
    ]

    def get(self, request, vimid="", tenantid="", portid=""):
        logger.debug("Ports--get::> %s" % request.data)
        try:
            # prepare request resource to vim instance
            req_resouce = "v2.0/ports"
            if portid:
                req_resouce += "/%s" % portid

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

            if not portid:
                # convert the key naming in ports
                for port in content["ports"]:
                    #use only 1 fixed_ip
                    port.update(port["fixed_ips"][0])
                    port.pop("fixed_ips", None)
                    VimDriverUtils.replace_key_by_mapping(port,
                                                          self.keys_mapping)
            else:
                # convert the key naming in the port specified by id
                tmp = content["port"]
                content.pop("port", None)
                #use only 1 fixed_ip
                tmp.update(tmp["fixed_ips"][0])
                tmp.pop("fixed_ips", None)
                VimDriverUtils.replace_key_by_mapping(tmp,
                                                      self.keys_mapping)
                content.update(tmp)

            return Response(data=content, status=resp.status_code)
        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except Exception as e:
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, vimid="", tenantid="", portid=""):
        logger.debug("Ports--post::> %s" % request.data)
        try:
            # prepare request resource to vim instance
            req_resouce = "v2.0/ports"

            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid)
            port = request.data
            #handle ip and subnetId
            if port["ip"] and port["subnetId"]:
                 fixed_ip = {
                    "ip_address": port["ip"],
                    "subnet_id": port["subnetId"],
                 }
                 port["fixed_ips"] = []
                 port["fixed_ips"].append(fixed_ip)

            port.pop("ip", None)
            port.pop("subnetId", None)

            VimDriverUtils.replace_key_by_mapping(port,
                                                  self.keys_mapping, True)
            req_body = json.JSONEncoder().encode({"port": port})
            resp = sess.post(req_resouce, data=req_body,
                             endpoint_filter=self.service)
            resp_body = resp.json()["port"]
            #use only 1 fixed_ip
            tmp = resp_body
            tmp.update(tmp["fixed_ips"][0])
            tmp.pop("fixed_ips", None)
            VimDriverUtils.replace_key_by_mapping(resp_body, self.keys_mapping)
            vim_dict = {
                "vimName": vim["name"],
                "vimId": vim["vimId"],
                "tenantId": tenantid,
            }
            resp_body.update(vim_dict)
            return Response(data=resp_body, status=resp.status_code)
        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except Exception as e:
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        pass

    def delete(self, request, vimid="", tenantid="", portid=""):
        logger.debug("Ports--delete::> %s" % request.data)
        try:
            # prepare request resource to vim instance
            req_resouce = "v2.0/ports"
            if portid:
                req_resouce += "/%s" % portid
#            query = VimDriverUtils.get_query_part(request)
#            if query:
#                req_resouce += "?%s" % query

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
