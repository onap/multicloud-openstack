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

from newton.pub.config import config
from newton.pub.exceptions import VimDriverNewtonException
from newton.requests.views.util import VimDriverUtils
from newton.pub.utils.restcall import req_to_aai
from newton.pub.msapi import extsys

logger = logging.getLogger(__name__)

DEBUG=True

class Registry(APIView):

    def __init__(self):
        self.proxy_prefix = config.MULTICLOUD_PREFIX
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

            self._logger.debug("update_tenant,vimid:%s_%s req_to_aai: %s, return %s, %s, %s"
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
        self._logger.debug("vimid: %s, req: %s,resp code: %s, body: %s"
                           % (vimid, req_resource, resp.status_code,content))

        if resp.status_code != status.HTTP_200_OK:
            return False  # failed to discover resources

        # iterate all projects and populate them into AAI
        cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)
        for tenant in content.get('projects'):
            tenant_info = {
                'tenant-id': tenant['id'],
                'tenant-name': tenant['name'],
            }
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

            self._logger.debug("update_flavor,vimid:%s_%s req_to_aai: %s, return %s, %s, %s"
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

        self._logger.debug("vimid: %s, req: %s,resp code: %s, body: %s"
                           % (vimid, req_resource, resp.status_code,content))

        if resp.status_code != status.HTTP_200_OK:
            return False  # failed to discover resources

        cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)
        for flavor in content.get('flavors'):
            flavor_info = {
                'flavor-id': flavor['id'],
                'flavor-name': flavor['name'],
                'flavor-vcpus': flavor['vcpus'],
                'flavor-ram': flavor['ram'],
                'flavor-disk': flavor['disk'],
                'flavor-ephemeral': flavor['OS-FLV-EXT-DATA:ephemeral'],
                'flavor-swap': flavor['swap'],
                'flavor-is-public': flavor['os-flavor-access:is_public'],
                'flavor-disabled': flavor['OS-FLV-DISABLED:disabled'],
            }

            if flavor.get('link') and len(flavor['link']) > 0:
                flavor_info['flavor-selflink'] =flavor['links'][0]['href'],

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
                req_to_aai(
                    "/cloud-infrastructure/cloud-regions/cloud-region"
                    + "/%s/%s/images/image/%s/metadata/metadatum/%s"
                    % (cloud_owner, cloud_region_id, image_id, metadatainfo['metaname']),
                    "PUT", content=metadatainfo)

            self._logger.debug("update_image,vimid:%s_%s req_to_aai: %s/%s, return %s, %s, %s"
                               % (cloud_owner,cloud_region_id,image_id,metadatainfo['metaname'],
                                  retcode, content, status_code))
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
                           % (cloud_owner, cloud_region_id, imageinfo['image-id']),
                           "PUT", content=imageinfo)

            self._logger.debug("update_image,vimid:%s_%s req_to_aai: %s, return %s, %s, %s"
                               % (cloud_owner,cloud_region_id, imageinfo['image-id'],
                                  retcode, content, status_code))

            return retcode
        return 1  # unknown cloud owner,region_id

    def discover_images(self, request, vimid="", session=None, viminfo=None):

        req_resource = "/v2/images"
        service = {'service_type': "image",
                   'interface': 'public',
                   'region_id': viminfo['cloud_region_id']}
        resp = session.get(req_resource, endpoint_filter=service)
        content = resp.json()

        self._logger.debug("vimid: %s, req: %s,resp code: %s, body: %s"
                           % (vimid, req_resource, resp.status_code,content))

        if resp.status_code != status.HTTP_200_OK:
            return False   # failed to discover resources

        cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)
        for image in content.get('images'):
            image_info = {
                'image-id': image['id'],
                'image-name': image['name'],
                'image-selflink': image['self'],

                'image-os-distro': image.get('os_distro'),
                'image-os-version': image.get('os_version'),
                'application': image.get('application'),
                'application-vendor': image.get('application_vendor'),
                'application-version': image.get('application_version'),
                'image-architecture': image.get('architecture'),
            }

            ret = self.update_image(cloud_owner, cloud_region_id, image_info)
            if ret != 0:
                # failed to update image
                self._logger.debug("failed to populate image info into AAI: %s, image id: %s, ret:%s"
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

                self._logger.debug("vimid: %s, req: %s,resp code: %s, body: %s"
                                   % (vimid, req_resource, resp.status_code, content))
                if resp.status_code == status.HTTP_200_OK:
                    # parse the schema? TBD
                    # self.update_image(cloud_owner, cloud_region_id, image_info)
                    #metadata_info = {}
                    pass
        pass


    def update_az(self, cloud_owner, cloud_region_id, azinfo):
        '''
        populate available zone into AAI
        :param cloud_owner:
        :param cloud_region_id:
        :param azinfo:
            availability-zone-name: string
            hypervisor-type: string
            operational-status: string
        :return:
        '''

        if cloud_owner and cloud_region_id:
            retcode, content, status_code = \
                req_to_aai(
                    "/cloud-infrastructure/cloud-regions/cloud-region"
                    + "/%s/%s/availability-zones/availability-zone/%s"
                    % (cloud_owner, cloud_region_id, azinfo['availability-zone-name']),
                    "PUT", content=azinfo)

            self._logger.debug("update_az,vimid:%s_%s req_to_aai: %s, return %s, %s, %s"
                               % (cloud_owner,cloud_region_id, azinfo['availability-zone-name'],
                                  retcode, content, status_code))

            return retcode
        return 1  # unknown cloud owner,region_id

    def discover_availablezones(self, request, vimid="", session=None, viminfo=None):

        req_resource = "/os-availability-zone/detail"
        service = {'service_type': "compute",
                   'interface': 'public',
                   'region_id': viminfo['cloud_region_id']}
        resp = session.get(req_resource, endpoint_filter=service)
        content = resp.json()
        self._logger.debug("vimid: %s, req: %s,resp code: %s, body: %s"
                           % (vimid, req_resource, resp.status_code,content))

        cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)
        for az in content.get('availabilityZoneInfo'):
            az_info = {
                'availability-zone-name': az['zoneName'],
                'operational-status': az['zoneState']['available'] if az.get('zoneState') else '',
                'hypervisor-type': '',
            }
            if az.get('hosts'):
                for (k, v) in az['hosts'].items():
                    req_resource = "/os-hypervisors/detail?hypervisor_hostname_pattern=%s" % k
                    service = {'service_type': "compute",
                               'interface': 'public',
                               'region_id': viminfo['cloud_region_id']}
                    resp = session.get(req_resource, endpoint_filter=service)
                    content = resp.json()
                    self._logger.debug("vimid: %s, req: %s,resp code: %s, body: %s"
                                       % (vimid, req_resource, resp.status_code, content))
                    if resp.status_code != status.HTTP_200_OK and not content[0]:
                        continue
                    az_info['hypervisor-type'] = content['hypervisors'][0]['hypervisor_type']\
                        if len(content.get('hypervisors')) else ''

                    break
            ret = self.update_az(cloud_owner, cloud_region_id, az_info)
            if ret != 0:
                # failed to update image
                self._logger.debug("failed to populate az info into AAI: %s, az name: %s, ret:%s"
                                   % (vimid, az_info['availability-zone-name'], ret))
            continue
        pass

    def update_vg(self, cloud_owner, cloud_region_id, vginfo):
        '''
        populate volume group into AAI
        :param cloud_owner:
        :param cloud_region_id:
        :param vginfo:
            volume-group-id: string
            volume-group-name: string
            vnf-type: string
            model-customization-id: string
            heat-stack-id: string
            orchestration-status: string
             vf-module-model-customization-id: string

        :return:
        '''


        if cloud_owner and cloud_region_id:
            retcode, content, status_code = \
                req_to_aai(
                    "/cloud-infrastructure/cloud-regions/cloud-region"
                    + "/%s/%s/volume-groups/volume-group/%s"
                    % (cloud_owner, cloud_region_id, vginfo['volume-group-id']),
                    "PUT", content=vginfo)

            self._logger.debug("update_vg,vimid:%s_%s req_to_aai: %s, return %s, %s, %s"
                               % (cloud_owner,cloud_region_id, vginfo['volume-group-id'],
                                  retcode, content, status_code))

            return retcode
        return 1  # unknown cloud owner,region_id

    def discover_volumegroups(self, request, vimid="", session=None, viminfo=None):

        req_resource = "/consistencygroups/detail"
        service = {'service_type': "volumev3",
                   'interface': 'public',
                   'region_id': viminfo['cloud_region_id']}
        resp = session.get(req_resource, endpoint_filter=service)
        content = resp.json()
        self._logger.debug("vimid: %s, req: %s,resp code: %s, body: %s"
                           % (vimid, req_resource, resp.status_code,content))

        cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)
        for cg in content.get('consistencygroups'):
            vg_info = {
                'volume-group-id': cg['id'],
                'volume-group-name': cg['name'],
                'vnf-type': '',
            }

            ret = self.update_az(cloud_owner, cloud_region_id, vg_info)
            if ret != 0:
                # failed to update image
                self._logger.debug("failed to populate volumegroup info into AAI: %s, volume-group-id: %s, ret:%s"
                                   % (vimid, vg_info['volume-group-id'], ret))
            continue
        pass

    def update_snapshot(self, cloud_owner, cloud_region_id, snapshotinfo):
        '''
        populate snapshot into AAI
        :param cloud_owner:
        :param cloud_region_id:
        :param snapshotinfo:
            snapshot-id: string
            snapshot-name: string
            snapshot-architecture: string
            snapshot-os-distro: string
            snapshot-os-version: string
            application: string
            application-vendor: string
            application-version: string
            snapshot-selflink: string
            prev-snapshot-id: string

        :return:
        '''

        if cloud_owner and cloud_region_id:
            retcode, content, status_code = \
                req_to_aai("/cloud-infrastructure/cloud-regions/cloud-region/%s/%s/volume-groups/volume-group/%s"
                           % (cloud_owner, cloud_region_id, snapshotinfo['snapshot-id']), "PUT", content=snapshotinfo)

            self._logger.debug("update_snapshot,vimid:%s_%s req_to_aai: %s, return %s, %s, %s"
                               % (cloud_owner,cloud_region_id, snapshotinfo['snapshot-id'], retcode, content, status_code))

            return retcode
        return 1  # unknown cloud owner,region_id

    def discover_snapshots(self, request, vimid="", session=None, viminfo=None):

        req_resource = "/snapshots/detail"
        service = {'service_type': "volumev3",
                   'interface': 'public',
                   'region_id': viminfo['cloud_region_id']}
        resp = session.get(req_resource, endpoint_filter=service)
        content = resp.json()

        self._logger.debug("vimid: %s, req: %s,resp code: %s, body: %s"
                           % (vimid, req_resource, resp.status_code,content))

        cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)
        for ss in content.get('snapshots'):
            snapshot_info = {
                'snapshot-id': ss['id'],
                'snapshot-name': ss['name'],
            }
            if ss.get('metadata'):
                snapshot_info['snapshot-architecture'] = ss['metadata'].get('architecture')
                snapshot_info['application'] = ss['metadata'].get('architecture')
                snapshot_info['snapshot-os-distro'] = ss['metadata'].get('os-distro')
                snapshot_info['snapshot-os-version'] = ss['metadata'].get('os-version')
                snapshot_info['application-vendor'] = ss['metadata'].get('vendor')
                snapshot_info['application-version'] = ss['metadata'].get('version')
                snapshot_info['snapshot-selflink'] = ss['metadata'].get('selflink')
                snapshot_info['prev-snapshot-id'] = ss['metadata'].get('prev-snapshot-id')

            ret = self.update_az(cloud_owner, cloud_region_id, snapshot_info)
            if ret != 0:
                # failed to update image
                self._logger.debug("failed to populate snapshot info into AAI: %s, snapshot-id: %s, ret:%s"
                                   % (vimid, snapshot_info['snapshot-id'], ret))
            continue
        pass

    def discover_servergroups(self, request, vimid="", session=None, viminfo=None):

        req_resource = "/os-server-groups"
        service = {'service_type': "compute",
                   'interface': 'public',
                   'region_id': viminfo['cloud_region_id']}
        resp = session.get(req_resource, endpoint_filter=service)
        content = resp.json()

        self._logger.debug("vimid: %s, req: %s,resp code: %s, body: %s"
                           % (vimid, req_resource, resp.status_code,content))
        pass


    def update_pserver(self, cloud_owner, cloud_region_id, pserverinfo):
        '''
        populate pserver into AAI
        :param cloud_owner:
        :param cloud_region_id:
        :param pserverinfo:
            hostname: string
            in-maint: boolean

            pserver-name2: string
            pserver-id: string
            ptnii-equip-name: string
            number-of-cpus: integer
            disk-in-gigabytes: integer
            ram-in-megabytes: integer
            equip-type: string
            equip-vendor: string
            equip-model: string
            fqdn: string
            pserver-selflink: string
            ipv4-oam-address: string
            serial-number: string
            ipaddress-v4-loopback-0: string
            ipaddress-v6-loopback-0: string
            ipaddress-v4-aim: string
            ipaddress-v6-aim: string
            ipaddress-v6-oam: string
            inv-status: string
            internet-topology: string
            purpose: string
            prov-status: string
            management-option: string
            host-profile: string

        :return:
        '''

        if cloud_owner and cloud_region_id:
            retcode, content, status_code = \
                req_to_aai("/cloud-infrastructure/pservers/pserver/%s"
                           % (pserverinfo['hostname']), "PUT", content=pserverinfo)

            self._logger.debug("update_snapshot,vimid:%s_%s req_to_aai: %s, return %s, %s, %s"
                               % (cloud_owner,cloud_region_id, pserverinfo['hostname'], retcode, content, status_code))

            if retcode == 0:
                # relationship to cloud-region

                related_link = ("%s/cloud-infrastructure/cloud-regions/"
                                "cloud-region/%s/%s" % (
                                    config.AAI_BASE_URL, cloud_owner,
                                    cloud_region_id))

                relationship_data = \
                    {
                        'related-to': 'cloud-region',
                        'related-link': related_link,
                        'relationship-data': [
                            {
                                'relationship-key': 'cloud-region.cloud-owner',
                                'relationship-value': cloud_owner
                            },
                            {
                                'relationship-key': 'cloud-region.cloud-region-id',
                                'relationship-value': cloud_region_id
                            }
                        ],
                        "related-to-property": [
                            {
                                "property-key": "cloud-region.cloud-owner"
                            },
                            {
                                "property-key": "cloud-region.cloud-region-id"
                            }
                        ]
                    }

                retcode, content, status_code = \
                    req_to_aai("/cloud-infrastructure/pservers/pserver/%s/relationship-list/relationship"
                               % (pserverinfo['hostname']), "PUT", content=relationship_data)

                self._logger.debug("update_pserver,vimid:%s_%s req_to_aai: %s, return %s, %s, %s"
                                   % (cloud_owner, cloud_region_id, pserverinfo['hostname'], retcode, content,
                                      status_code))
                pass

            return retcode
        return 1  # unknown cloud owner,region_id

    def discover_pservers(self, request, vimid="", session=None, viminfo=None):

        req_resource = "/os-hypervisors/detail"
        service = {'service_type': "compute",
                   'interface': 'public',
                   'region_id': viminfo['cloud_region_id']}
        resp = session.get(req_resource, endpoint_filter=service)
        content = resp.json()

        self._logger.debug("vimid: %s, req: %s,resp code: %s, body: %s"
                           % (vimid, req_resource, resp.status_code,content))

        cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)
        for hypervisor in content.get('hypervisors'):
            hypervisor_info = {
                'hostname': hypervisor['hypervisor_hostname'],
                'in-maint': hypervisor['state'],

                'pserver-id': hypervisor.get('id'),
                'ptnii-equip-name': hypervisor.get('id'),
                'disk-in-gigabytes': hypervisor.get('local_gb'),
                'ram-in-megabytes': hypervisor.get('memory_mb'),
                'pserver-selflink': hypervisor.get('hypervisor_links'),
                'ipv4-oam-address': hypervisor.get('host_ip'),
            }

            if hypervisor.get('cpu_info') and hypervisor.get('cpu_info').get('topology'):
                cputopo = hypervisor.get('cpu_info').get('topology')
                n_cpus = cputopo['cores'] * cputopo['threads'] * cputopo['sockets']
                hypervisor_info['number-of-cpus'] = n_cpus

            ret = self.update_pserver(cloud_owner, cloud_region_id, hypervisor_info)
            if ret != 0:
                # failed to update image
                self._logger.debug("failed to populate pserver info into AAI: %s, hostname: %s, ret:%s"
                                   % (vimid, hypervisor_info['hostname'], ret))
            continue
        pass


    def update_epa_caps(self, cloud_owner, cloud_region_id, epa_caps_info):
        '''
        populate cloud EPA Capabilities information into AAI
        :param cloud_owner:
        :param cloud_region_id:
        :param epa_caps_info: dict of meta data about cloud-region's epa caps

        :return:
        '''

        cloud_epa_caps = {
            'cloud-epa-caps': json.dumps(epa_caps_info),
        }

        if cloud_owner and cloud_region_id:
            retcode, content, status_code = \
                req_to_aai("/cloud-infrastructure/cloud-regions/cloud-region/%s/%s/"
                           % (cloud_owner, cloud_region_id, ), "PUT", content=cloud_epa_caps)

            self._logger.debug(
                "update_epa_caps,vimid:%s_%s req_to_aai: update cloud-epa-caps, return %s, %s, %s"
                % (cloud_owner,cloud_region_id, retcode, content, status_code))

            return retcode
        return 1  # unknown cloud owner,region_id

    def discover_epa_resources(self, request, vimid="", session=None, viminfo=None):
        cloud_epa_caps_info = {}
        cloud_extra_info = viminfo.get('cloud_extra_info')
        if cloud_extra_info:
            cloud_epa_caps_info.update(json.loads(cloud_extra_info))
            pass

        cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)
        ret = self.update_epa_caps(cloud_owner, cloud_region_id, cloud_epa_caps_info)
        if ret != 0:
            # failed to update image
            self._logger.debug("failed to populate EPA CAPs info into AAI: %s, ret:%s"
                               % (vimid, ret))

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

            self._logger.debug("update_proxy_identity_endpoint,vimid:%s_%s req_to_aai: %s, return %s, %s, %s"
                               % (cloud_owner,cloud_region_id, url, retcode, content, status_code))

    def post(self, request, vimid=""):
        self._logger.debug("Registration--post::data> %s" % request.data)
        self._logger.debug("Registration--post::vimid > %s" % vimid)

        try:
            # populate proxy identity url
            cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)
            self.update_proxy_identity_endpoint(cloud_owner, cloud_region_id,
                                                self.proxy_prefix + "/%s/identity/v3" % vimid)

            # prepare request resource to vim instance
            # get token:
            viminfo = VimDriverUtils.get_vim_info(vimid)
            # set the default tenant since there is no tenant info in the VIM yet
            sess = VimDriverUtils.get_session(viminfo, tenantname=request.data['defaultTenant'])

            # step 1. discover all projects and populate into AAI
            self.discover_tenants(request, vimid,sess, viminfo)

            # discover all flavors
            self.discover_flavors(request, vimid, sess, viminfo)

            # discover all images
            self.discover_images(request, vimid, sess, viminfo)

            # discover all az
            self.discover_availablezones(request, vimid, sess, viminfo)

            # discover all vg
            #self.discover_volumegroups(request, vimid, sess, viminfo)

            # discover all snapshots
            self.discover_snapshots(request, vimid, sess, viminfo)

            # discover all server groups
            #self.discover_servergroups(request, vimid, sess, viminfo)

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
            return Response(status=status.HTTP_202_ACCEPTED if ret_code==0 else status.HTTP_500_INTERNAL_SERVER_ERROR)
        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
