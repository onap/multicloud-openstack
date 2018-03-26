# Copyright 2018 CMCC Technologies Co.,Ltd
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
import threading
import traceback
from keystoneauth1.exceptions import HttpError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import VimDriverNewtonException
from newton_base.util import VimDriverUtils

logger = logging.getLogger(__name__)

running_threads = {}
running_thread_lock = threading.Lock()


class VMlist(APIView):
    service = {'service_type': 'compute',
               'interface': 'public'}
    keys_mapping = [
        ("project_id", "tenantId"),
        ("disk_format", "serverType"),
        ("container_format", "containerFormat")
    ]

    def get(self, request, vimid="", tenantid="", serverid=""):
        logger.debug("servers--get::> %s" % request.data)
        try:
            query = VimDriverUtils.get_query_part(request)
            content, status_code = self.get_servers(query, vimid, tenantid, serverid)
            return Response(data=content, status=status_code)
        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

							
    def get_servers(self, query="", vimid="", tenantid="", serverid=""):
        logger.debug("servers--get_servers::> %s" % serverid)

        req_resouce = "/servers"
        vim = VimDriverUtils.get_vim_info(vimid)
        vim["domain"] = "Default"
        sess = VimDriverUtils.get_session(vim, tenantid)
        resp = sess.get(req_resouce, endpoint_filter=self.service)
        content = resp.json()
        vim_dict = {
            "vimName": vim["name"],
            "vimId": vim["vimId"],
            "tenantId": tenantid,
        }

        return content, resp.status_code

    
