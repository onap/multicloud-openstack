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
from newton.pub.utils.restcall import req_to_aai
from newton.pub.msapi import extsys

logger = logging.getLogger(__name__)

DEBUG=True

class Registry(APIView):

    def __init__(self):
        self._logger = logger


    def update_tenant(self, cloud_owner, cloud_region_id, tenantinfo):
        '''
        populate tenant into AAI
        :param cloud_owner:
        :param cloud_region_id:
        :param tenantinfo:
            tenant-id: string
            tenant-name: string
        :return:
        '''


        if cloud_owner and cloud_region_id:
            retcode, content, status_code = \
                req_to_aai("/cloud-infrastructure/cloud-regions/cloud-region/%s/%s/tenants/tenant/%s"
                           % (cloud_owner, cloud_region_id, tenantinfo['tenant-id']), "PUT", content=tenantinfo)

            self._logger.debug("update_tenant,vimid:%s_%s req_to_aai: %s, return %s, %s, %s" \
                               % (cloud_owner,cloud_region_id, tenantinfo['tenant-id'], retcode, content, status_code))
            return retcode
        return 1

    def discover_tenants(self, request, vimid="", session=None, viminfo=None):
        req_resource = "/projects"
        service = {'service_type': "identity",
                   'interface': 'public',
                   'region_id': viminfo['cloud_region_id']}

        resp = session.get(req_resource, endpoint_filter=service)
        content = resp.json()
        self._logger.debug("vimid: %s, req: %s,resp code: %s, body: %s" \
                           % (vimid, req_resource, resp.status_code,content))

        if resp.status_code != status.HTTP_200_OK:
            return False #failed to discover resources

        # iterate all projects and populate them into AAI
        cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)
        tenant_info = {}
        for tenant in content['projects']:
            tenant_info['tenant-id'] = tenant['id']
            tenant_info['tenant-name'] = tenant['name']
            self.update_tenant(cloud_owner, cloud_region_id, tenant_info)

        pass


    def update_flavor(self, cloud_owner, cloud_region_id, flavorinfo):
        '''
        populate flavor into AAI
        :param cloud_owner:
        :param cloud_region_id:
        :param flavorinfo:
            flavor-id: string
            flavor-name: string
            flavor-vcpus: integer
            flavor-ram: integer
            flavor-disk: integer
            flavor-ephemeral: integer
            flavor-swap: string
            flavor-is-public: boolean
            flavor-selflink: string
            flavor-disabled: boolean

        :return:
        '''

        if cloud_owner and cloud_region_id:
            retcode, content, status_code = \
                req_to_aai("/cloud-infrastructure/cloud-regions/cloud-region/%s/%s/flavors/flavor/%s"
                           % (cloud_owner, cloud_region_id, flavorinfo['flavor-id']), "PUT", content=flavorinfo)

            self._logger.debug("update_flavor,vimid:%s_%s req_to_aai: %s, return %s, %s, %s" \
                               % (cloud_owner,cloud_region_id, flavorinfo['flavor-id'], retcode, content, status_code))
            return retcode
        return 1

    def discover_flavors(self, request, vimid="", session=None, viminfo=None):

        req_resource = "/flavors/detail"
        service = {'service_type': "compute",
                   'interface': 'public',
                   'region_id': viminfo['cloud_region_id']}
        resp = session.get(req_resource, endpoint_filter=service)
        content = resp.json()

        self._logger.debug("vimid: %s, req: %s,resp code: %s, body: %s" \
                           % (vimid, req_resource, resp.status_code,content))

        if resp.status_code != status.HTTP_200_OK:
            return False #failed to discover resources

        cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)
        flavor_info = {}
        for flavor in content['flavors']:
            flavor_info['flavor-id'] = flavor['id']
            flavor_info['flavor-name'] = flavor['name']
            flavor_info['flavor-vcpus'] = flavor['vcpus']
            flavor_info['flavor-ram'] = flavor['ram']
            flavor_info['flavor-disk'] = flavor['disk']
            flavor_info['flavor-ephemeral'] = flavor['OS-FLV-EXT-DATA:ephemeral']
            flavor_info['flavor-swap'] = flavor['swap']
            flavor_info['flavor-is-public'] = flavor['os-flavor-access:is_public']
            flavor_info['flavor-selflink'] = flavor['links'][0]['href']
            flavor_info['flavor-swap'] = flavor['swap']
            flavor_info['flavor-disabled'] = flavor['OS-FLV-DISABLED:disabled']
            self.update_flavor(cloud_owner, cloud_region_id, flavor_info)

        pass

    def update_image_metadata(self, cloud_owner, cloud_region_id, image_id, metadatainfo):
        '''
        populate image meta data
        :param cloud_owner:
        :param cloud_region_id:
        :param image_id:
        :param metadatainfo:
            metaname: string
            metaval: string
        :return:
        '''

        if cloud_owner and cloud_region_id:
            retcode, content, status_code = \
                req_to_aai("/cloud-infrastructure/cloud-regions/cloud-region/%s/%s/images/image/%s"
                           % (cloud_owner, cloud_region_id, image_id, metadatainfo['metaname']), "PUT", content=imageinfo)

            self._logger.debug("update_image,vimid:%s_%s req_to_aai: %s/%s, return %s, %s, %s" \
                               % (cloud_owner,cloud_region_id,image_id,metadatainfo['metaname'], retcode, content, status_code))
            return retcode
        return 1

    def update_image(self, cloud_owner, cloud_region_id, imageinfo):
        '''
        populate image into AAI
        :param cloud_owner:
        :param cloud_region_id:
        :param imageinfo:
            image-id: string
            image-name: string
            image-architecture: string
            image-os-distro: string
            image-os-version: string
            application: string
            application-vendor: string
            application-version: string
            image-selflink: string

        :return:
        '''


        if cloud_owner and cloud_region_id:
            retcode, content, status_code = \
                req_to_aai("/cloud-infrastructure/cloud-regions/cloud-region/%s/%s/images/image/%s"
                           % (cloud_owner, cloud_region_id, imageinfo['image-id']), "PUT", content=imageinfo)

            self._logger.debug("update_image,vimid:%s_%s req_to_aai: %s, return %s, %s, %s" \
                               % (cloud_owner,cloud_region_id, imageinfo['image-id'], retcode, content, status_code))

            return retcode
        return 1 #unknown cloud owner,region_id

    def discover_images(self, request, vimid="", session=None, viminfo=None):

        req_resource = "/v2/images"
        service = {'service_type': "image",
                   'interface': 'public',
                   'region_id': viminfo['cloud_region_id']}
        resp = session.get(req_resource, endpoint_filter=service)
        content = resp.json()

        self._logger.debug("vimid: %s, req: %s,resp code: %s, body: %s" \
                           % (vimid, req_resource, resp.status_code,content))

        if resp.status_code != status.HTTP_200_OK:
            return False #failed to discover resources

        cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)
        image_info = {}
        metadata_info = {}
        for image in content['images']:
            image_info['image-id'] = image['id']
            image_info['image-name'] = image['name']
            image_info['image-selflink'] = image['self']

            image_info['image-os-distro'] = image['os_distro'] or ''
            image_info['image-os-version'] = image['os_version'] or ''
            image_info['application'] = image['application'] or ''
            image_info['application-vendor'] = image['application_vendor'] or ''
            image_info['application-version'] = image['application_version'] or ''
            image_info['image-architecture'] = image['architecture'] or ''

            ret = self.update_image(cloud_owner, cloud_region_id, image_info)
            if ret != 0:
                #failed to update image
                self._logger.debug("failed to populate image info into AAI: %s, image id: %s, ret:%s" \
                                   % (vimid, image_info['image-id'], ret))
                continue

            schema = image['schema']
            if schema:
                req_resource = schema
                service = {'service_type': "image",
                           'interface': 'public',
                           'region_id': viminfo['cloud_region_id']}
                resp = session.get(req_resource, endpoint_filter=service)
                content = resp.json()

                self._logger.debug("vimid: %s, req: %s,resp code: %s, body: %s" \
                                   % (vimid, req_resource, resp.status_code, content))
                if resp.status_code == status.HTTP_200_OK:
                    #parse the schema?
                    #self.update_image(cloud_owner, cloud_region_id, image_info)
                    pass




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

    def update_proxy_identity_endpoint(self, cloud_owner, cloud_region_id, url):
        '''
        update cloud_region's identity url
        :param cloud_owner:
        :param cloud_region_id:
        :param url:
        :return:
        '''
        if cloud_owner and cloud_region_id:
            retcode, content, status_code = \
                req_to_aai("/cloud-infrastructure/cloud-regions/cloud-region/%s/%s"
                           % (cloud_owner, cloud_region_id), "PUT", content={'identity-url': url})

            self._logger.debug("update_proxy_identity_endpoint,vimid:%s_%s req_to_aai: %s, return %s, %s, %s" \
                               % (cloud_owner,cloud_region_id, url, retcode, content, status_code))

    def post(self, request, vimid=""):
        self._logger.debug("Registration--post::data> %s" % request.data)
        self._logger.debug("Registration--post::vimid > %s" % vimid)

        try:
            #populate proxy identity url
            cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)
            self.update_proxy_identity_endpoint(cloud_owner, cloud_region_id, config.MULTICLOUD_PREFIX+"/%s/identity/v3" % vimid )

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
