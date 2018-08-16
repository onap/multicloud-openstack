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


class Hosts(APIView):
    service = {'service_type': 'compute',
               'interface': 'public'}

    hosts_keys_mapping = [
        ("host_name", "name"),
    ]
    host_keys_mapping = [
        ("host", "name"),
    ]

    def get(self, request, vimid="", tenantid="", hostname=""):
        logger.info("vimid, tenantid, hostname = %s,%s,%s" % (vimid, tenantid, hostname))
        if request.data:
            logger.debug("With data = %s" % request.data)
            pass
        try:
            #prepare request resource to vim instance
            req_resouce = "/os-hosts"
            if hostname:
                req_resouce += "/%s" % hostname

            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid)

            self.service['region_id'] = vim['openstack_region_id'] \
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
                "tenantId": tenantid,
            }
            content.update(vim_dict)


            if not hostname:
                # convert the key naming in hosts
                for host in content["hosts"]:
                    VimDriverUtils.replace_key_by_mapping(host,
                                                          self.hosts_keys_mapping)
            else:
                #restructure host data model
                old_host = content["host"]
                content["host"] = []
                # convert the key naming in resources
                for res in old_host:
                    VimDriverUtils.replace_key_by_mapping(res['resource'],
                                                          self.host_keys_mapping)
                    content["host"].append(res['resource'])

            logger.info("response with status = %s" % resp.status_code)

            return Response(data=content, status=resp.status_code)

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


class APIv1Hosts(Hosts):

    def get(self, request, cloud_owner="", cloud_region_id="", tenantid="", hostname=""):
        self._logger.info("%s, %s" % (cloud_owner, cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1Hosts, self).get(request, vimid, tenantid, hostname)
