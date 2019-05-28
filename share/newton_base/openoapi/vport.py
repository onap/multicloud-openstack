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

    def __init__(self):
        super(Vports, self).__init__()
        self._logger = logger

    def get(self, request, vimid="", tenantid="", portid=""):
        logger.info("vimid, tenantid, portid = %s,%s,%s" % (vimid, tenantid, portid))
        if request.data:
            logger.debug("With data = %s" % request.data)
            pass
        try:
            # prepare request resource to vim instance
            querystr = VimDriverUtils.get_query_part(request)
            query = "project_id=%s" % (tenantid)
            if querystr:
                query += "&" + querystr

            content, status_code = self._get_ports(query, vimid, tenantid, portid)
            logger.info("response with status = %s" % status_code)
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

    def _get_ports(self, query="", vimid="", tenantid="", portid=""):
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
        logger.info("vimid, tenantid, portid = %s,%s,%s" % (vimid, tenantid, portid))
        if request.data:
            logger.debug("With data = %s" % request.data)
            pass
        try:
            #check if already created: name
            query = "project_id=%s&name=%s" % (tenantid, request.data["name"])
            networkid = request.data.get("networkId", None)
            if networkid:
                query += "&network_id=%s" % networkid
            content, status_code = self._get_ports(query, vimid, tenantid, portid)
            existed = False
            if status_code == 200:
                for port in content["ports"]:
                    if port["name"] == request.data["name"]:
                        existed = True
                        break
                if existed == True:
                    vim_dict = {
                         "returnCode": 0,
                    }
                    port.update(vim_dict)
                    return Response(data=port, status=status_code)

            #otherwise create a new one
            return self._create_port(request, vimid, tenantid)
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

    def _create_port(self, request, vimid, tenantid):
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
                port["fixed_ips"] = []
                for one_tmpip in tmpip.split(','):
                    fixed_ip = {
                        "ip_address": one_tmpip,
                        "subnet_id": tmpsubnet,
                    }
                    port["fixed_ips"].append(fixed_ip)

            VimDriverUtils.replace_key_by_mapping(port,
                                                  self.keys_mapping, True)
            req_body = json.JSONEncoder().encode({"port": port})
            logger.info("making request with URI:%s" % req_resouce)
            logger.debug("with data:%s" % req_body)
            resp = sess.post(req_resouce, data=req_body,
                             endpoint_filter=self.service)
            logger.info("request returns with status %s" % resp.status_code)
            resp_body = resp.json()["port"]
            #use only 1 fixed_ip
            tmpips = resp_body.pop("fixed_ips", None)
            if tmpips and len(tmpips) > 0:
                resp_body.update(tmpips[0])

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
        return {}

    def delete(self, request, vimid="", tenantid="", portid=""):
        logger.info("vimid, tenantid, portid = %s,%s,%s" % (vimid, tenantid, portid))
        if request.data:
            logger.debug("With data = %s" % request.data)
            pass
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


class APIv1Vports(Vports):

    def __init__(self):
        super(APIv1Vports, self).__init__()
        self._logger = logger

    def get(self, request, cloud_owner="", cloud_region_id="", tenantid="", portid=""):
        self._logger.info("%s, %s" % (cloud_owner, cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1Vports, self).get(request, vimid, tenantid, portid)

    def post(self, request, cloud_owner="", cloud_region_id="", tenantid="", portid=""):
        self._logger.info("%s, %s" % (cloud_owner, cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1Vports, self).post(request, vimid, tenantid, portid)

    def delete(self, request, cloud_owner="", cloud_region_id="", tenantid="", portid=""):
        self._logger.info("%s, %s" % (cloud_owner, cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1Vports, self).delete(request, vimid, tenantid, portid)
