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


class Subnets(APIView):
    service = {'service_type': 'network',
               'interface': 'public',
               'region_name': 'RegionOne'}
    keys_mapping = [
        ("project_id", "tenantId"),
        ("network_id", "networkId"),
        ("ip_version", "ipVersion"),
        ("enable_dhcp", "enableDhcp"),
        ("gateway_ip", "gatewayIp"),
        ("dns_nameservers", "dnsNameservers"),
        ("host_routes", "hostRoutes"),
        ("allocation_pools", "allocationPools"),
    ]

    def get(self, request, vimid="", tenantid="", subnetid=""):
        logger.debug("Subnets--get::> %s" % request.data)
        try:
            # prepare request resource to vim instance
            query = VimDriverUtils.get_query_part(request)
            content, status_code = self.get_subnets(query, vimid, tenantid, subnetid)
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

    def get_subnets(self, query="", vimid="", tenantid="", subnetid=""):
        logger.debug("Subnets--get_subnets::> %s" % subnetid)

        # prepare request resource to vim instance
        req_resouce = "v2.0/subnets"
        if subnetid:
            req_resouce += "/%s" % subnetid

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

        if not subnetid:
            # convert the key naming in subnets
            for subnet in content["subnets"]:
                VimDriverUtils.replace_key_by_mapping(subnet,
                                                      self.keys_mapping)
        else:
            # convert the key naming in the subnet specified by id
            subnet = content.pop("subnet", None)
            VimDriverUtils.replace_key_by_mapping(subnet,
                                                  self.keys_mapping)
            content.update(subnet)

        return content, resp.status_code

    def post(self, request, vimid="", tenantid="", subnetid=""):
        logger.debug("Subnets--post::> %s" % request.data)
        try:
            #check if created already: check name
            query = "name=%s" % request.data["name"]
            content, status_code = self.get_subnets(query, vimid, tenantid)
            existed = False
            if status_code == 200:
                for subnet in content["subnets"]:
                    if subnet["name"] == request.data["name"]:
                        existed = True
                        break
                    pass
                if existed == True:
                    vim_dict = {
                        "returnCode": 0,
                    }
                    subnet.update(vim_dict)
                    return Response(data=subnet, status=status_code)

            # prepare request resource to vim instance
            req_resouce = "v2.0/subnets"

            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid)
            subnet = request.data
            VimDriverUtils.replace_key_by_mapping(subnet,
                                                  self.keys_mapping, True)
            req_body = json.JSONEncoder().encode({"subnet": subnet})
            resp = sess.post(req_resouce, data=req_body,
                             endpoint_filter=self.service)
            resp_body = resp.json()["subnet"]
            VimDriverUtils.replace_key_by_mapping(resp_body, self.keys_mapping)
            vim_dict = {
                "vimName": vim["name"],
                "vimId": vim["vimId"],
                "tenantId": tenantid,
                "returnCode": 1,
            }
            resp_body.update(vim_dict)
            return Response(data=resp_body, status=resp.status_code)
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

    def delete(self, request, vimid="", tenantid="", subnetid=""):
        logger.debug("Subnets--delete::> %s" % request.data)
        try:
            # prepare request resource to vim instance
            req_resouce = "v2.0/subnets"
            if subnetid:
                req_resouce += "/%s" % subnetid
            query = VimDriverUtils.get_query_part(request)
            if query:
                req_resouce += "?%s" % query

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
