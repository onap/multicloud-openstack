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

from common.exceptions import VimDriverNewtonException

from newton_base.util import VimDriverUtils
from common.msapi import extsys

logger = logging.getLogger(__name__)


class Subnets(APIView):
    service = {'service_type': 'network',
               'interface': 'public'}
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

    def __init__(self):
        super(Subnets, self).__init__()
        self._logger = logger

    def get(self, request, vimid="", tenantid="", subnetid=""):
        logger.info("vimid, tenantid, subnetid = %s,%s,%s" % (vimid, tenantid, subnetid))
        if request.data:
            logger.debug("With data = %s" % request.data)
            pass
        try:
            # prepare request resource to vim instance
            querystr = VimDriverUtils.get_query_part(request)
            query = "project_id=%s" % (tenantid)
            if querystr:
                query += "&" + querystr

            content, status_code = self._get_subnets(query, vimid, tenantid, subnetid)
            logger.info("request returns with status %s" % status_code)
            return Response(data=content, status=status_code)
        except VimDriverNewtonException as e:
            logger.error("response with status = %s" % e.status_code)
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_subnets(self, query="", vimid="", tenantid="", subnetid=""):

        # prepare request resource to vim instance
        req_resouce = "v2.0/subnets"
        if subnetid:
            req_resouce += "/%s" % subnetid

        if query:
            req_resouce += "?%s" % query

        vim = VimDriverUtils.get_vim_info(vimid)
        sess = VimDriverUtils.get_session(vim, tenantid)

        self.service['region_name'] = vim['openstack_region_id'] \
            if vim.get('openstack_region_id') \
            else vim['cloud_region_id']

        logger.info("making request with URI:%s" % req_resouce)
        resp = sess.get(req_resouce, endpoint_filter=self.service)
        logger.info("request returns with status %s" % resp.status_code)
        if resp.status_code == status.HTTP_200_OK:
            logger.debug("with content:%s" % resp.json())
            pass
        content = resp.json()
        vim_dict = {
            "vimName": vim["name"],
            "vimId": vim["vimId"],
            "cloud-owner": vim["cloud_owner"],
            "cloud-region-id": vim["cloud_region_id"],
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
        logger.info("vimid, tenantid, subnetid = %s,%s,%s" % (vimid, tenantid, subnetid))
        if request.data:
            logger.debug("With data = %s" % request.data)
            pass
        try:
            #check if created already: check name
            query = "project_id=%s&name=%s" % (tenantid, request.data["name"])
            networkid = request.data.get("networkId", None)
            if networkid:
                query += "&network_id=%s" % networkid

            content, status_code = self._get_subnets(query, vimid, tenantid)
            existed = False
            if status_code == 200:
                for subnet in content["subnets"]:
                    if subnet["name"] == request.data["name"]:
                        existed = True
                        break
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

            self.service['region_name'] = vim['openstack_region_id'] \
                if vim.get('openstack_region_id') \
                else vim['cloud_region_id']

            logger.info("making request with URI:%s" % req_resouce)
            logger.debug("with data:%s" % req_body)
            resp = sess.post(req_resouce, data=req_body,
                             endpoint_filter=self.service)
            logger.info("request returns with status %s" % resp.status_code)
            resp_body = resp.json()["subnet"]
            VimDriverUtils.replace_key_by_mapping(resp_body, self.keys_mapping)
            vim_dict = {
                "vimName": vim["name"],
                "vimId": vim["vimId"],
                "cloud-owner": vim["cloud_owner"],
                "cloud-region-id": vim["cloud_region_id"],
                "tenantId": tenantid,
                "returnCode": 1,
            }
            resp_body.update(vim_dict)
            return Response(data=resp_body, status=resp.status_code)
        except VimDriverNewtonException as e:
            logger.error("response with status = %s" % e.status_code)
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, vimid="", tenantid="", subnetid=""):
        logger.info("vimid, tenantid, subnetid = %s,%s,%s" % (vimid, tenantid, subnetid))
        if request.data:
            logger.debug("With data = %s" % request.data)
            pass
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

            self.service['region_name'] = vim['openstack_region_id'] \
                if vim.get('openstack_region_id') \
                else vim['cloud_region_id']

            logger.info("making request with URI:%s" % req_resouce)
            resp = sess.delete(req_resouce, endpoint_filter=self.service)
            logger.info("request returns with status %s" % resp.status_code)
            return Response(status=resp.status_code)
        except VimDriverNewtonException as e:
            logger.error("response with status = %s" % e.status_code)
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class APIv1Subnets(Subnets):

    def __init__(self):
        super(APIv1Subnets, self).__init__()
        self._logger = logger

    def get(self, request, cloud_owner="", cloud_region_id="", tenantid="", subnetid=""):
        self._logger.info("%s, %s" % (cloud_owner, cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1Subnets, self).get(request, vimid, tenantid, subnetid)

    def post(self, request, cloud_owner="", cloud_region_id="", tenantid="", subnetid=""):
        self._logger.info("%s, %s" % (cloud_owner, cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1Subnets, self).post(request, vimid, tenantid, subnetid)

    def delete(self, request, cloud_owner="", cloud_region_id="", tenantid="", subnetid=""):
        self._logger.info("%s, %s" % (cloud_owner, cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1Subnets, self).delete(request, vimid, tenantid, subnetid)
