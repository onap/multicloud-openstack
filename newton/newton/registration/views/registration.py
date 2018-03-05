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

from keystoneauth1.exceptions import HttpError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from newton.pub.config import config
from newton.pub.exceptions import VimDriverNewtonException
from newton.pub.msapi import extsys
from newton.pub.utils import restcall
from newton.requests.views.util import VimDriverUtils

logger = logging.getLogger(__name__)


class Registry(APIView):

    def __init__(self):
        self.proxy_prefix = config.MULTICLOUD_PREFIX
        self._logger = logger

    def _get_list_resources(
            self, resource_url, service_type, session, viminfo,
            vimid, content_key):
        service = {'service_type': service_type,
                   'interface': 'public',
                   'region_id': viminfo['cloud_region_id']}
        resp = session.get(resource_url, endpoint_filter=service)
        content = resp.json()

        self._logger.debug("vimid: %s, req: %s,resp code: %s, body: %s"
                           % (vimid, resource_url, resp.status_code,content))

        if resp.status_code != status.HTTP_200_OK:
            return  # failed to discover resources
        return content.get(content_key)

    def _update_resoure(self, cloud_owner, cloud_region_id,
                        resoure_id, resource_info, resource_type):
        if cloud_owner and cloud_region_id:
            self._logger.debug(
                ("_update_resoure,vimid:%(cloud_owner)s"
                 "_%(cloud_region_id)s req_to_aai: %(resoure_id)s, "
                 "%(resource_type)s, %(resource_info)s")
                % {
                    "cloud_owner": cloud_owner,
                    "cloud_region_id": cloud_region_id,
                    "resoure_id": resoure_id,
                    "resource_type": resource_type,
                    "resource_info": resource_info,
                })

            #get the resource first
            resource_url = ("/cloud-infrastructure/cloud-regions/"
                     "cloud-region/%(cloud_owner)s/%(cloud_region_id)s/"
                     "%(resource_type)ss/%(resource_type)s/%(resoure_id)s"
                     % {
                         "cloud_owner": cloud_owner,
                         "cloud_region_id": cloud_region_id,
                         "resoure_id": resoure_id,
                         "resource_type": resource_type,
                     })

            # get cloud-region
            retcode, content, status_code = \
                restcall.req_to_aai(resource_url, "GET")

            # add resource-version
            if retcode == 0 and content:
                content = json.JSONDecoder().decode(content)
                #resource_info["resource-version"] = content["resource-version"]
                content.update(resource_info)
                resource_info = content

            #then update the resource
            retcode, content, status_code = \
                restcall.req_to_aai(resource_url, "PUT", content=resource_info)

            self._logger.debug(
                ("_update_resoure,vimid:%(cloud_owner)s"
                 "_%(cloud_region_id)s req_to_aai: %(resoure_id)s, "
                 "return %(retcode)s, %(content)s, %(status_code)s")
                % {
                    "cloud_owner": cloud_owner,
                    "cloud_region_id": cloud_region_id,
                    "resoure_id": resoure_id,
                    "retcode": retcode,
                    "content": content,
                    "status_code": status_code,
                })
            return retcode
        return 1  # unknown cloud owner,region_id

    def _discover_tenants(self, vimid="", session=None, viminfo=None):
        try:
            # iterate all projects and populate them into AAI
            cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)
            for tenant in self._get_list_resources(
                    "projects", "identity", session, viminfo, vimid,
                    "projects"):
                tenant_info = {
                    'tenant-id': tenant['id'],
                    'tenant-name': tenant['name'],
                }
                self._update_resoure(
                    cloud_owner, cloud_region_id, tenant['id'],
                    tenant_info, "tenant")

        except VimDriverNewtonException as e:
            self._logger.error("VimDriverNewtonException: status:%s, response:%s" % (e.http_status, e.content))
            return
        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return

    def _discover_flavors(self, vimid="", session=None, viminfo=None):
        try:
            cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)
            for flavor in self._get_list_resources(
                    "/flavors/detail", "compute", session, viminfo, vimid,
                    "flavors"):
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
                    flavor_info['flavor-selflink'] = flavor['link'][0]['href'] or 'http://0.0.0.0',
                else:
                    flavor_info['flavor-selflink'] = 'http://0.0.0.0',

                self._update_resoure(
                    cloud_owner, cloud_region_id, flavor['id'],
                    flavor_info, "flavor")

        except VimDriverNewtonException as e:
            self._logger.error("VimDriverNewtonException: status:%s, response:%s" % (e.http_status, e.content))
            return
        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return

    # def update_image_metadata(self, cloud_owner, cloud_region_id, image_id, metadatainfo):
    #     '''
    #     populate image meta data
    #     :param cloud_owner:
    #     :param cloud_region_id:
    #     :param image_id:
    #     :param metadatainfo:
    #         metaname: string
    #         metaval: string
    #     :return:
    #     '''
    #
    #     if cloud_owner and cloud_region_id:
    #         retcode, content, status_code = \
    #             restcall.req_to_aai(
    #                 "/cloud-infrastructure/cloud-regions/cloud-region"
    #                 + "/%s/%s/images/image/%s/metadata/metadatum/%s"
    #                 % (cloud_owner, cloud_region_id, image_id, metadatainfo['metaname']),
    #                 "PUT", content=metadatainfo)
    #
    #         self._logger.debug("update_image,vimid:%s_%s req_to_aai: %s/%s, return %s, %s, %s"
    #                            % (cloud_owner,cloud_region_id,image_id,metadatainfo['metaname'],
    #                               retcode, content, status_code))
    #         return retcode
    #     return 1

    def _discover_images(self, vimid="", session=None, viminfo=None):
        try:
            cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)
            for image in self._get_list_resources(
                    "/v2/images", "image", session, viminfo, vimid,
                    "images"):
                image_info = {
                    'image-id': image['id'],
                    'image-name': image['name'],
                    'image-selflink': image['self'],

                    'image-os-distro': image.get('os_distro') or 'Unknown',
                    'image-os-version': image.get('os_version') or 'Unknown',
                    'application': image.get('application'),
                    'application-vendor': image.get('application_vendor'),
                    'application-version': image.get('application_version'),
                    'image-architecture': image.get('architecture'),
                }

                ret = self._update_resoure(
                    cloud_owner, cloud_region_id, image['id'], image_info,
                    "image")
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
                    # if resp.status_code == status.HTTP_200_OK:
                        # parse the schema? TBD
                        # self.update_image(cloud_owner, cloud_region_id, image_info)
                        #metadata_info = {}

        except VimDriverNewtonException as e:
            self._logger.error("VimDriverNewtonException: status:%s, response:%s" % (e.http_status, e.content))
            return
        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return

    def _discover_availability_zones(self, vimid="", session=None,
                                     viminfo=None):
        try:
            cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)
            for az in self._get_list_resources(
                    "/os-availability-zone/detail", "compute", session,
                    viminfo, vimid,
                    "availabilityZoneInfo"):
                az_info = {
                    'availability-zone-name': az['zoneName'],
                    'operational-status': az['zoneState']['available']
                    if az.get('zoneState') else '',
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
                ret = self._update_resoure(
                    cloud_owner, cloud_region_id, az['zoneName'], az_info,
                    "availability-zone")
                if ret != 0:
                    # failed to update image
                    self._logger.debug("failed to populate az info into AAI: %s, az name: %s, ret:%s"
                                       % (vimid, az_info['availability-zone-name'], ret))

        except VimDriverNewtonException as e:
            self._logger.error("VimDriverNewtonException: status:%s, response:%s" % (e.http_status, e.content))
            return
        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return

    # def _discover_volumegroups(self, vimid="", session=None, viminfo=None):
    #     cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)
    #     for cg in self._get_list_resources(
    #             "/consistencygroups/detail", "volumev3", session,
    #             viminfo, vimid,
    #             "consistencygroups"):
    #         vg_info = {
    #             'volume-group-id': cg['id'],
    #             'volume-group-name': cg['name'],
    #             'vnf-type': '',
    #         }
    #
    #         ret = self._update_resoure(
    #             cloud_owner, cloud_region_id, cg['id'], vg_info,
    #             "volume-group")
    #         if ret != 0:
    #             # failed to update image
    #             self._logger.debug("failed to populate volumegroup info into AAI: %s, volume-group-id: %s, ret:%s"
    #                                % (vimid, vg_info['volume-group-id'], ret))

    def _discover_snapshots(self, vimid="", session=None, viminfo=None):
        try:
            cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)
            for ss in self._get_list_resources(
                    "/snapshots/detail", "volumev3", session,
                    viminfo, vimid,
                    "snapshots"):
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

                ret = self._update_resoure(
                    cloud_owner, cloud_region_id, ss['id'], snapshot_info,
                    "snapshot")
                if ret != 0:
                    # failed to update image
                    self._logger.debug("failed to populate snapshot info into AAI: %s, snapshot-id: %s, ret:%s"
                                       % (vimid, snapshot_info['snapshot-id'], ret))

        except VimDriverNewtonException as e:
            self._logger.error("VimDriverNewtonException: status:%s, response:%s" % (e.http_status, e.content))
            return
        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return

    # def _discover_servergroups(self, vimid="", session=None, viminfo=None):
    #     for sg in self._get_list_resources(
    #             "/os-server-groups", "compute", session,
    #             viminfo, vimid,
    #             "security groups"):

    def _update_pserver(self, cloud_owner, cloud_region_id, pserverinfo):
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
            resource_url = "/cloud-infrastructure/pservers/pserver/%s" \
                           % (pserverinfo['hostname'])

            # get cloud-region
            retcode, content, status_code = \
                restcall.req_to_aai(resource_url, "GET")

            # add resource-version to url
            if retcode == 0 and content:
                content = json.JSONDecoder().decode(content)
                #pserverinfo["resource-version"] = content["resource-version"]
                content.update(pserverinfo)
                pserverinfo = content


            retcode, content, status_code = \
                restcall.req_to_aai(resource_url, "PUT", content=pserverinfo)

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
                    restcall.req_to_aai("/cloud-infrastructure/pservers/pserver/%s/relationship-list/relationship"
                               % (pserverinfo['hostname']), "PUT", content=relationship_data)

                self._logger.debug("update_pserver,vimid:%s_%s req_to_aai: %s, return %s, %s, %s"
                                   % (cloud_owner, cloud_region_id, pserverinfo['hostname'], retcode, content,
                                      status_code))

            return retcode
        return 1  # unknown cloud owner,region_id

    def _discover_pservers(self, vimid="", session=None, viminfo=None):
        try:
            cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)
            for hypervisor in self._get_list_resources(
                    "/os-hypervisors/detail", "compute", session,
                    viminfo, vimid,
                    "hypervisors"):
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

    #            if hypervisor.get('cpu_info') and hypervisor['cpu_info'].get('topology'):
    #                cputopo = hypervisor['cpu_info'].get('topology')
    #                n_cpus = cputopo['cores'] * cputopo['threads'] * cputopo['sockets']
    #                hypervisor_info['number-of-cpus'] = n_cpus
                if hypervisor.get('cpu_info'):
                    cpu_info = json.loads(hypervisor['cpu_info'])
                    if cpu_info.get('topology'):
                        cputopo = cpu_info.get('topology')
                        n_cpus = cputopo['cores'] * cputopo['threads'] * cputopo['sockets']
                        hypervisor_info['number-of-cpus'] = n_cpus

                ret = self._update_pserver(cloud_owner, cloud_region_id,
                                          hypervisor_info)
                if ret != 0:
                    # failed to update image
                    self._logger.debug("failed to populate pserver info into AAI: %s, hostname: %s, ret:%s"
                                       % (vimid, hypervisor_info['hostname'], ret))

        except VimDriverNewtonException as e:
            self._logger.error("VimDriverNewtonException: status:%s, response:%s" % (e.http_status, e.content))
            return
        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return

    def _update_epa_caps(self, cloud_owner, cloud_region_id, epa_caps_info):
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
            resource_url = "/cloud-infrastructure/cloud-regions/cloud-region/%s/%s" \
                           % (cloud_owner, cloud_region_id)

            # get cloud-region
            retcode, content, status_code = \
                restcall.req_to_aai(resource_url, "GET")

            #add resource-version to url
            if retcode == 0 and content:
                content = json.JSONDecoder().decode(content)
                #cloud_epa_caps["resource-version"] = content["resource-version"]
                content.update(cloud_epa_caps)
                cloud_epa_caps = content

            #update cloud-region
            retcode, content, status_code = \
                restcall.req_to_aai(resource_url, "PUT", content=cloud_epa_caps)

            self._logger.debug(
                "update_epa_caps,vimid:%s_%s req_to_aai: update cloud-epa-caps, return %s, %s, %s"
                % (cloud_owner,cloud_region_id, retcode, content, status_code))

            return retcode
        return 1  # unknown cloud owner,region_id

    def _discover_epa_resources(self, vimid="", viminfo=None):
        try:
            cloud_epa_caps_info = {}
            cloud_extra_info_str = viminfo.get('cloud_extra_info')
            if cloud_extra_info_str:
                cloud_extra_info = json.loads(cloud_extra_info_str)
                cloud_epa_caps_info.update(cloud_extra_info.get("epa-caps"))

            cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)
            ret = self._update_epa_caps(cloud_owner, cloud_region_id,
                                        cloud_epa_caps_info)
            if ret != 0:
                # failed to update image
                self._logger.debug("failed to populate EPA CAPs info into AAI: %s, ret:%s"
                                   % (vimid, ret))

        except VimDriverNewtonException as e:
            self._logger.error("VimDriverNewtonException: status:%s, response:%s" % (e.http_status, e.content))
            return
        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return

    def _update_proxy_identity_endpoint(self, vimid):
        '''
        update cloud_region's identity url
        :param cloud_owner:
        :param cloud_region_id:
        :param url:
        :return:
        '''
        try:
            cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)
            if cloud_owner and cloud_region_id:
                resource_url = "/cloud-infrastructure/cloud-regions/cloud-region/%s/%s" \
                               % (cloud_owner, cloud_region_id)

                # get cloud-region
                retcode, content, status_code = \
                    restcall.req_to_aai(resource_url, "GET")

                # add resource-version to url
                if retcode == 0 and content:
                    viminfo = json.JSONDecoder().decode(content)
                    # cloud_epa_caps["resource-version"] = content["resource-version"]
                    viminfo['identity-url'] = self.proxy_prefix + "/%s/identity/v2.0" % vimid

                    retcode, content, status_code = \
                        restcall.req_to_aai("/cloud-infrastructure/cloud-regions/cloud-region/%s/%s"
                                   % (cloud_owner, cloud_region_id), "PUT", content=viminfo)

                    self._logger.debug("update_proxy_identity_endpoint,vimid:%s req_to_aai: %s, return %s, %s, %s"
                                       % (vimid, viminfo['identity-url'], retcode, content, status_code))
                else:
                    self._logger.debug("failure: update_proxy_identity_endpoint,vimid:%s req_to_aai: return %s, %s, %s"
                                       % (vimid, retcode, content, status_code))

        except VimDriverNewtonException as e:
            self._logger.error("VimDriverNewtonException: status:%s, response:%s" % (e.http_status, e.content))
            return
        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return

    def post(self, request, vimid=""):
        self._logger.debug("Registration--post::data> %s" % request.data)
        self._logger.debug("Registration--post::vimid > %s" % vimid)

        try:
            # populate proxy identity url
            self._update_proxy_identity_endpoint(vimid)

            # prepare request resource to vim instance
            # get token:
            viminfo = VimDriverUtils.get_vim_info(vimid)
            if not viminfo:
                raise VimDriverNewtonException(
                    "There is no cloud-region with {cloud-owner}_{cloud-region-id}=%s in AAI" % vimid)

            # set the default tenant since there is no tenant info in the VIM yet
            sess = VimDriverUtils.get_session(
                viminfo, tenant_name=viminfo['tenant'])

            # step 1. discover all projects and populate into AAI
            self._discover_tenants(vimid, sess, viminfo)

            # discover all flavors
            self._discover_flavors(vimid, sess, viminfo)

            # discover all images
            self._discover_images(vimid, sess, viminfo)

            # discover all az
            self._discover_availability_zones(vimid, sess, viminfo)

            # discover all vg
            #self._discover_volumegroups(vimid, sess, viminfo)

            # discover all snapshots
            self._discover_snapshots(vimid, sess, viminfo)

            # discover all server groups
            #self.discover_servergroups(request, vimid, sess, viminfo)

            # discover all pservers
            self._discover_pservers(vimid, sess, viminfo)

            # discover all epa resources, e.g. sriov pf and vf, etc.
            self._discover_epa_resources(vimid, viminfo)

            return Response(status=status.HTTP_202_ACCEPTED)

        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return Response(
                data={'error': str(e)},
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
