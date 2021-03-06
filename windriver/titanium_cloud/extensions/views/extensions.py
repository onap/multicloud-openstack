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
import traceback

from keystoneauth1.exceptions import HttpError
from rest_framework import status
from rest_framework.response import Response
# from rest_framework.views import APIView

from django.conf import settings
from common.exceptions import VimDriverNewtonException
from common.msapi import extsys
from newton_base.extensions import extensions as newton_extensions

LOGGER = logging.getLogger(__name__)

# DEBUG=True


class Extensions(newton_extensions.Extensions):

    def __init__(self):
        super(Extensions, self).__init__()
        # self._logger = LOGGER
        self.proxy_prefix = settings.MULTICLOUD_PREFIX

    def get(self, request, vimid=""):
        LOGGER.debug("Extensions--get::data> %s" % request.data)
        LOGGER.debug("Extensions--get::vimid> %s"
                     % vimid)
        try:
            cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)
            registered_extensions = \
                [
                    # {
                    #     "alias": "guest-monitor",
                    #     "description": "Multiple network support",
                    #     "name": "Guest Monitor",
                    #     "url": self.proxy_prefix + "/%s/extensions/guest-monitor/{server_id}" % (vimid),
                    #     "spec": ""
                    # }
                ]

            content = {
                "cloud-owner": cloud_owner,
                "cloud-region-id": cloud_region_id,
                "vimid": vimid,
                "extensions": registered_extensions
            }
            return Response(data=content, status=status.HTTP_200_OK)

        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            LOGGER.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            LOGGER.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class APIv1Extensions(Extensions):

    def __init__(self):
        super(APIv1Extensions, self).__init__()
        # self._logger = LOGGER
        self.proxy_prefix = settings.MULTICLOUD_API_V1_PREFIX

    def get(self, request, cloud_owner="", cloud_region_id=""):
        LOGGER.info(
            "cloud_owner,cloud_region_id: %s,%s" %
            (cloud_owner, cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1Extensions, self).get(request, vimid)
