# Copyright 2017-2018 Wind River Systems, Inc.
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
from newton.pub.msapi import extsys

logger = logging.getLogger(__name__)

DEBUG=True


class Extensions(APIView):

    def __init__(self):
        self.proxy_prefix = config.MULTICLOUD_PREFIX
        self._logger = logger

    def get(self, request, vimid=""):
        logger.debug("Extensions--get::data> %s" % request.data)
        logger.debug("Extensions--get::vimid> %s"
                     % vimid)
        try:
            cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)
            registered_extensions = \
                [
                    {
                        "alias": "epa-caps",
                        "description": "Multiple network support",
                        "name": "EPACapsQuery",
                        "url": self.proxy_prefix + "/%s/extensions/epa-caps" \
                                       % (vimid),
                        "spec": ""
                    }
                ]

            content = {
                "cloud-owner":cloud_owner,
                "cloud-region-id":cloud_region_id,
                "vimid":vimid,
                "extensions": registered_extensions
            }
            return Response(data=content, status=status.HTTP_200_OK)

        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
