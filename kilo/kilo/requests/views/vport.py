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

from kilo.pub.exceptions import VimDriverKiloException

from util import VimDriverUtils

logger = logging.getLogger(__name__)


class Vports(APIView):
    service = {'service_type': 'network',
               'interface': 'public'}
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
            query = VimDriverUtils.get_query_part(request)
            content, status_code = self.get_ports(query, vimid, tenantid, portid)

            return Response(data=content, status=status_code)
        except VimDriverKiloException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_ports(self, query="", vimid="", tenantid="", portid=""):
        logger.debug("Ports--get_ports::> %s" % portid)
        vim = VimDriverUtils.get_vim_info(vimid)
        sess = VimDriverUtils.get_session(vim, tenantid)

        if sess:
            # prepare request resource to vim instance
            req_resouce = "v2.0/ports"
            if portid:
                req_resouce += "/%s" % portid

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
                    # use only 1st entry of fixed_ips
                    tmpips = port.pop("fixed_ips", None) if port else None
                    port.update(tmpips[0]) if tmpips and len(tmpips) > 0 else None
                    VimDriverUtils.replace_key_by_mapping(port,
                                                          self.keys_mapping)
            else:
                # convert the key naming in the port specified by id
                port = content.pop("port", None)
                #use only 1st entry of fixed_ips
                tmpips = port.pop("fixed_ips", None) if port else None
                port.update(tmpips[0]) if tmpips and len(tmpips) > 0 else None

                VimDriverUtils.replace_key_by_mapping(port,
                                                      self.keys_mapping)
                content.update(port)
            return content, resp.status_code
        return {}, 500

    def post(self, request, vimid="", tenantid="", portid=""):
        logger.debug("Ports--post::> %s" % request.data)
        try:
            #check if already created: name
            query = "name=%s" % request.data["name"]
            content, status_code = self.get_ports(query, vimid, tenantid, portid)
            existed = False
            if status_code == 200:
                for port in content["ports"]:
                    if port["name"] == request.data["name"]:
                        existed = True
                        break
                    pass
                if existed == True:
                    vim_dict = {
                         "returnCode": 0,
                    }
                    port.update(vim_dict)
                    return Response(data=port, status=status_code)

            #otherwise create a new one
            return self.create_port(request, vimid, tenantid)
        except VimDriverKiloException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create_port(self, request, vimid, tenantid):
        logger.debug("Ports--create::> %s" % request.data)
        vim = VimDriverUtils.get_vim_info(vimid)
        sess = VimDriverUtils.get_session(vim, tenantid)
        if sess:
            # prepare request resource to vim instance
            req_resouce = "v2.0/ports"

            port = request.data
            #handle ip and subnetId
            tmpip = port.pop("ip", None)
            tmpsubnet = port.pop("subnetId", None)
            if tmpip and tmpsubnet:
                 fixed_ip = {
                    "ip_address": tmpip,
                    "subnet_id": tmpsubnet,
                 }
                 port["fixed_ips"] = []
                 port["fixed_ips"].append(fixed_ip)

            VimDriverUtils.replace_key_by_mapping(port,
                                                  self.keys_mapping, True)
            req_body = json.JSONEncoder().encode({"port": port})
            resp = sess.post(req_resouce, data=req_body,
                             endpoint_filter=self.service)
            resp_body = resp.json()["port"]
            #use only 1 fixed_ip
            tmpips = resp_body.pop("fixed_ips", None)
            if tmpips and len(tmpips) > 0:
                resp_body.update(tmpips[0])

            VimDriverUtils.replace_key_by_mapping(resp_body, self.keys_mapping)
            vim_dict = {
                "vimName": vim["name"],
                "vimId": vim["vimId"],
                "tenantId": tenantid,
                "returnCode": 1,
            }
            resp_body.update(vim_dict)
            return Response(data=resp_body, status=resp.status_code)
        return {}

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
        except VimDriverKiloException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        pass
