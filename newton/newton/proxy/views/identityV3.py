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

from django.core.cache import cache

from keystoneauth1 import access
from keystoneauth1.access import service_catalog
from keystoneauth1.exceptions import HttpError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from newton.pub.config import config
from newton.pub.exceptions import VimDriverNewtonException
from newton.requests.views.util import VimDriverUtils
from newton.proxy.views.proxy_utils import ProxyUtils

logger = logging.getLogger(__name__)

DEBUG=True

class Tokens(APIView):
    service = {'service_type': 'identity',
               'interface': 'public'}

    def __init__(self):
        self.proxy_prefix = config.MULTICLOUD_PREFIX
        self._logger = logger

    def post(self, request, vimid=""):
        self._logger.debug("identityV3--post::META> %s" % request.META)
        self._logger.debug("identityV3--post::data> %s" % request.data)
        self._logger.debug("identityV3--post::vimid> %s" % (vimid))
        sess = None
        resp = None
        resp_body = None
        try:
            # prepare request resource to vim instance
            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim)

            tmp_auth_state = VimDriverUtils.get_auth_state(vim, sess)
            tmp_auth_info = json.loads(tmp_auth_state)
            tmp_auth_token = tmp_auth_info['auth_token']
            tmp_auth_data = tmp_auth_info['body']

            #store the auth_state, redis/memcached
            #set expiring in 1 hour

            #update the catalog
            tmp_auth_data['token']['catalog'], tmp_metadata_catalog = ProxyUtils.update_catalog(vimid, tmp_auth_data['token']['catalog'], self.proxy_prefix)
            tmp_auth_token = VimDriverUtils.update_token_cache(vim, sess, tmp_auth_token, tmp_auth_state, json.dumps(tmp_metadata_catalog))

            resp = Response(headers={'X-Subject-Token': tmp_auth_token}, data=tmp_auth_data, status=status.HTTP_201_CREATED)
            return resp
        except VimDriverNewtonException as e:

            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            self._logger.error(traceback.format_exc())

            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

