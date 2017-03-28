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


class Hosts(APIView):
    service = {'service_type': 'compute',
               'interface': 'public',
               'region_name': 'RegionOne'}

    hosts_keys_mapping = [
        ("host_name", "name"),
    ]
    host_keys_mapping = [
        ("host", "name"),
    ]

    def get(self, request, vimid="", tenantid="", hostname=""):
        logger.debug("Hosts--get::> %s" % request.data)
        try:
            #prepare request resource to vim instance
            req_resouce = "/os-hosts"
            if hostname:
                req_resouce += "/%s" % hostname

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

            return Response(data=content, status=resp.status_code)
        except VimDriverKiloException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

