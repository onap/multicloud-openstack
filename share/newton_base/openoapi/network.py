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
from keystoneauth1.exceptions import HttpError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import VimDriverNewtonException

from newton_base.util import VimDriverUtils
from common.msapi import extsys

logger = logging.getLogger(__name__)


class Networks(APIView):
    service = {'service_type': 'network',
               'interface': 'public'}
    keys_mapping = [
        ("provider:segmentation_id", "segmentationId"),
        ("provider:physical_network", "physicalNetwork"),
        ("router:external", "routerExternal"),
        ("provider:network_type", "networkType"),
        ("vlan_transparent", "vlanTransparent"),
        ("project_id", "tenantId"),
    ]

    def __init__(self):
        super(Networks, self).__init__()
        self._logger = logger

    def get(self, request, vimid="", tenantid="", networkid=""):
        logger.info("vimid, tenantid, networkid = %s,%s,%s" % (vimid, tenantid, networkid))
        if request.data:
            logger.debug("With data = %s" % request.data)
            pass
        try:
            querystr = VimDriverUtils.get_query_part(request)
            query = "project_id=%s" % (tenantid)
            if querystr:
                query += "&" + querystr

            content, status_code = self._get_networks(query, vimid, tenantid, networkid)
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

    def _get_networks(self, query, vimid="", tenantid="", networkid=""):

        # prepare request resource to vim instance
        req_resouce = "v2.0/networks"
        if networkid:
            req_resouce += "/%s" % networkid

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
        logger.info("vimid, tenantid, networkid = %s,%s,%s" % (vimid, tenantid, networkid))
        if request.data:
            logger.debug("With data = %s" % request.data)
            pass
        try:
            #check if created already: check name
            query = "project_id=%s&name=%s" % (tenantid, request.data["name"])
            content, status_code = self._get_networks(query, vimid, tenantid)
            existed = False
            if status_code == 200:
                for network in content["networks"]:
                    if network["name"] == request.data["name"]:
                        existed = True
                        break
                if existed == True:
                    vim_dict = {
                        "returnCode": 0,
                    }
                    network.update(vim_dict)
                    return Response(data=network, status=status_code)

            # prepare request resource to vim instance
            req_resouce = "v2.0/networks"

            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid)
            network = request.data
            VimDriverUtils.replace_key_by_mapping(network,
                                                  self.keys_mapping, True)
            req_body = json.JSONEncoder().encode({"network": network})

            self.service['region_name'] = vim['openstack_region_id'] \
                if vim.get('openstack_region_id') \
                else vim['cloud_region_id']

            logger.info("making request with URI:%s" % req_resouce)
            logger.debug("with data:%s" % req_body)
            resp = sess.post(req_resouce, data=req_body,
                             endpoint_filter=self.service)
            logger.info("request returns with status %s" % resp.status_code)

            resp_body = resp.json()["network"]
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

    def delete(self, request, vimid="", tenantid="", networkid=""):
        logger.info("vimid, tenantid, networkid = %s,%s,%s" % (vimid, tenantid, networkid))
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

            self.service['region_name'] = vim['openstack_region_id'] \
                if vim.get('openstack_region_id') \
                else vim['cloud_region_id']

            logger.info("making delete request with URI:%s" % req_resouce)
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


class APIv1Networks(Networks):

    def __init__(self):
        super(APIv1Networks, self).__init__()
        self._logger = logger

    def get(self, request, cloud_owner="", cloud_region_id="", tenantid="", networkid=""):
        self._logger.info("%s, %s" % (cloud_owner, cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1Networks, self).get(request, vimid, tenantid, networkid)

    def post(self, request, cloud_owner="", cloud_region_id="", tenantid="", networkid=""):
        self._logger.info("%s, %s" % (cloud_owner, cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1Networks, self).post(request, vimid, tenantid, networkid)

    def delete(self, request, cloud_owner="", cloud_region_id="", tenantid="", networkid=""):
        self._logger.info("%s, %s" % (cloud_owner, cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1Networks, self).delete(request, vimid, tenantid, networkid)
