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

    def __init__(self):
        self._logger = logger

    def discover_tenants(self, request, vimid="", session=None, viminfo=None):
        req_resource = "/projects"
        service = {'service_type': "identity",
                   'interface': 'public',
                   'region_id': viminfo['cloud_region_id']}

        resp = session.get(req_resource, endpoint_filter=service)
        content = resp.json()
        self._logger.debug("vimid: %s, req: %s,resp code: %s, body: %s" \
                           % (vimid, req_resource, resp.status_code,content))
        # iterate all projects and populate them into AAI
        # TBD

        pass

    def discover_flavors(self, request, vimid="", session=None, viminfo=None):

        req_resource = "/flavors"
        service = {'service_type': "compute",
                   'interface': 'public',
                   'region_id': viminfo['cloud_region_id']}
        resp = session.get(req_resource, endpoint_filter=service)
        content = resp.json()

        self._logger.debug("vimid: %s, req: %s,resp code: %s, body: %s" \
                           % (vimid, req_resource, resp.status_code,content))
        pass

    def discover_images(self, request, vimid="", session=None, viminfo=None):

        req_resource = "/v2/images"
        service = {'service_type': "image",
                   'interface': 'public',
                   'region_id': viminfo['cloud_region_id']}
        resp = session.get(req_resource, endpoint_filter=service)
        content = resp.json()

        self._logger.debug("vimid: %s, req: %s,resp code: %s, body: %s" \
                           % (vimid, req_resource, resp.status_code,content))
        pass

    def discover_availablezones(self, request, vimid="", session=None, viminfo=None):

        req_resource = "/os-availability-zone/detail"
        service = {'service_type': "compute",
                   'interface': 'public',
                   'region_id': viminfo['cloud_region_id']}
        resp = session.get(req_resource, endpoint_filter=service)
        content = resp.json()
        self._logger.debug("vimid: %s, req: %s,resp code: %s, body: %s" \
                           % (vimid, req_resource, resp.status_code,content))
        pass

    def discover_volumegroups(self, request, vimid="", session=None, viminfo=None):

        req_resource = "/consistencygroups/detail"
        service = {'service_type': "volumev3",
                   'interface': 'public',
                   'region_id': viminfo['cloud_region_id']}
        resp = session.get(req_resource, endpoint_filter=service)
        content = resp.json()
        self._logger.debug("vimid: %s, req: %s,resp code: %s, body: %s" \
                           % (vimid, req_resource, resp.status_code,content))
        pass

    def discover_snapshots(self, request, vimid="", session=None, viminfo=None):

        req_resource = "/snapshots/detail"
        service = {'service_type': "volumev3",
                   'interface': 'public',
                   'region_id': viminfo['cloud_region_id']}
        resp = session.get(req_resource, endpoint_filter=service)
        content = resp.json()

        self._logger.debug("vimid: %s, req: %s,resp code: %s, body: %s" \
                           % (vimid, req_resource, resp.status_code,content))
        pass

    def discover_servergroups(self, request, vimid="", session=None, viminfo=None):

        req_resource = "/os-server-groups"
        service = {'service_type': "compute",
                   'interface': 'public',
                   'region_id': viminfo['cloud_region_id']}
        resp = session.get(req_resource, endpoint_filter=service)
        content = resp.json()

        self._logger.debug("vimid: %s, req: %s,resp code: %s, body: %s" \
                           % (vimid, req_resource, resp.status_code,content))
        pass

    def discover_pservers(self, request, vimid="", session=None, viminfo=None):

        req_resource = "/os-hypervisors/detail"
        service = {'service_type': "compute",
                   'interface': 'public',
                   'region_id': viminfo['cloud_region_id']}
        resp = session.get(req_resource, endpoint_filter=service)
        content = resp.json()

        self._logger.debug("vimid: %s, req: %s,resp code: %s, body: %s" \
                           % (vimid, req_resource, resp.status_code,content))
        pass


    def discover_epa_resources(self, request, vimid="", session=None, viminfo=None):


        pass

    def post(self, request, vimid=""):
        self._logger.debug("Registration--post::data> %s" % request.data)
        self._logger.debug("Registration--post::vimid > %s" % vimid)

        try:
            # prepare request resource to vim instance
            # get token:
            viminfo = VimDriverUtils.get_vim_info(vimid)
            #set the default tenant since there is no tenant info in the VIM yet
            sess = VimDriverUtils.get_session(viminfo, tenantname=request.data['defaultTenant'])

            #step 1. discover all projects and populate into AAI
            self.discover_tenants(request,vimid,sess, viminfo)

            # discover all flavors
            self.discover_flavors(request, vimid, sess, viminfo)

            # discover all images
            self.discover_images(request, vimid, sess, viminfo)


            # discover all az
            self.discover_availablezones(request, vimid, sess, viminfo)

            # discover all vg
            self.discover_volumegroups(request, vimid, sess, viminfo)

            # discover all snapshots
            self.discover_snapshots(request, vimid, sess, viminfo)

            # discover all server groups
            self.discover_servergroups(request, vimid, sess, viminfo)

            # discover all pservers
            self.discover_pservers(request, vimid, sess, viminfo)

            # discover all epa resources, e.g. sriov pf and vf, etc.
            self.discover_epa_resources(request, vimid, sess, viminfo)

            return Response(status=status.HTTP_202_ACCEPTED)

        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, vimid=""):
        self._logger.debug("Registration--delete::data> %s" % request.data)
        self._logger.debug("Registration--delete::vimid > %s"% vimid)
        try:
            ret_code = VimDriverUtils.delete_vim_info(vimid)
            return Response(status=status.HTTP_202_ACCEPTED)
        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
