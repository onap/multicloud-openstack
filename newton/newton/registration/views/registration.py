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

from newton.pub.exceptions import VimDriverNewtonException
from newton.requests.views.util import VimDriverUtils

logger = logging.getLogger(__name__)

DEBUG=True

class Registry(APIView):

    def post(self, request, vimid=""):
        logger.debug("Registration--post::data> %s" % request.data)
        logger.debug("Registration--post::vimid > %s" % vimid)

        try:
            # prepare request resource to vim instance
            # get token:
            vim = VimDriverUtils.get_vim_info(vimid)
            #set the default tenant since there is no tenant info in the VIM yet
            sess = VimDriverUtils.get_session(vim, tenantname=request.data['defaultTenant'])

            #step 1. discover all projects and populate into AAI
            req_resource = "/projects"
            service = {'service_type': "identity",
                       'interface': 'public',
                       'region_id': vim['cloud_region_id']}

            resp = sess.get(req_resource, endpoint_filter=service)
            content = resp.json()
            #iterate all projects and populate them into AAI
            # TBD

            # discover all flavors
            # discover all images
            # discover all az
            # discover all vg
            # discover all snapshots
            # discover all server groups
            # discover all pservers
            # discover all epa resources, e.g. sriov pf and vf, etc.

            return Response(status=status.HTTP_202_ACCEPTED)

        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, vimid=""):
        logger.debug("Registration--delete::data> %s" % request.data)
        logger.debug("Registration--delete::vimid > %s"% vimid)
        try:
            ret_code = VimDriverUtils.delete_vim_info(vimid)
            return Response(status=status.HTTP_202_ACCEPTED)
        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
