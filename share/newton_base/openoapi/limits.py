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

logger = logging.getLogger(__name__)


class Limits(APIView):
    service = {'service_type': 'compute',
               'interface': 'public'}

    service_network = {'service_type': 'network',
               'interface': 'public'}

    service_volume = {'service_type': 'volumev2',
               'interface': 'public'}

    def get(self, request, vimid="", tenantid=""):
        logger.info("vimid, tenantid = %s,%s" % (vimid, tenantid))
        if request.data:
            logger.debug("With data = %s" % request.data)
            pass
        try:
            #get limits first
            # prepare request resource to vim instance
            req_resouce = "/limits"
            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid)
            logger.info("making request with URI:%s" % req_resouce)
            resp = sess.get(req_resouce, endpoint_filter=self.service)
            logger.info("request returns with status %s" % resp.status_code)
            content = resp.json()
            content_all =content['limits']['absolute']

            vim_dict = {
                "vimName": vim["name"],
                "vimId": vim["vimId"],
                "tenantId": tenantid,
            }
            content_all.update(vim_dict)

            #now get quota
            # prepare request resource to vim instance
            req_resouce = "/v2.0/quotas/%s" % tenantid
            logger.info("making request with URI:%s" % req_resouce)
            resp = sess.get(req_resouce, endpoint_filter=self.service_network)
            logger.info("request returns with status %s" % resp.status_code)
            content = resp.json()
            content_all.update(content['quota'])

            #now get volume limits
            # prepare request resource to vim instance
            req_resouce = "/limits"
            logger.info("making request with URI:%s" % req_resouce)
            resp = sess.get(req_resouce, endpoint_filter=self.service_volume)
            logger.info("request returns with status %s" % resp.status_code)
            content = resp.json()
            content_all.update(content['limits']['absolute'])

            logger.info("response with status = %s" % resp.status_code)
            return Response(data=content_all, status=resp.status_code)
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

