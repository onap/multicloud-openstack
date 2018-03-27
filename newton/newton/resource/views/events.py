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

from rest_framework import status

from django.conf import settings
from common.exceptions import VimDriverNewtonException
from newton_base.util import VimDriverUtils

from keystoneauth1.exceptions import HttpError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from common.msapi import extsys


logger = logging.getLogger(__name__)


class EventsCheck(APIView):

    def __init__(self):
        self._logger = logger

    def post(self, request, vimid=""):
        self._logger.info("vimid, data> %s, %s" % (vimid, request.data))
        self._logger.debug("META> %s" % request.META)

        try :
            resource_demand = request.data

            # get token:
            cloud_owner, regionid = extsys.decode_vim_id(vimid)
            interface = 'public'
            service = {'service_type': 'compute',
                       'interface': interface,
                       'region_id': regionid}

            tenant_name = None
            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenant_name)

            # get servers detail info
            req_resouce = "/servers/detail"
            self._logger.info("check servers detail> URI:%s" % req_resouce)
            resp = sess.get(req_resouce, endpoint_filter=service)
            self._logger.info("check servers detail> status:%s" % resp.status_code)
            content = resp.json()
            self._logger.debug("check servers detail> resp data:%s" % content)

            # extract server status info
            if len(content['servers']):
                servers = content['servers']
                resp_vmstate = []
                for num in range(0, len(servers)):
                    vmstate = {
                        'name' : servers[num]['name'],
                        'state' : servers[num]['OS-EXT-STS:vm_state'],
                        'power_state' : servers[num]['OS-EXT-STS:power_state'],
                        'launched_at' : servers[num]['OS-SRV-USG:launched_at'],
                        'id' : servers[num]['id'],
                        'host' : servers[num]['OS-EXT-SRV-ATTR:host'],
                        'availability_zone' : servers[num]['OS-EXT-AZ:availability_zone'],
                        'tenant_id' : servers[num]['tenant_id']
                    }

                    resp_vmstate.append(vmstate)

            self._logger.info("RESP with data> result:%s" % resp_vmstate)
            return Response(data={'result': resp_vmstate}, status=status.HTTP_200_OK)

        except VimDriverNewtonException as e:
            self._logger.error("Plugin exception> status:%s,error:%s"
                                  % (e.status_code, e.content))
            return Response(data={'result': resp_vmstate,'error': e.content}, status=e.status_code)

        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            resp = e.response.json()
            resp.update({'result': resp_vmstate})
            return Response(data=e.response.json(), status=e.http_status)

        except Exception as e:
            self._logger.error(traceback.format_exc())
            return Response(data={'result': resp_vmstate, 'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

