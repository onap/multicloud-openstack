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
import json
import uuid
import traceback

from keystoneauth1.exceptions import HttpError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import VimDriverNewtonException
from common.msapi import extsys
from common.utils import restcall
from newton_base.util import VimDriverUtils

logger = logging.getLogger(__name__)


class Registry(APIView):

    def __init__(self):
        self.proxy_prefix = "multicloud"
        self.aai_base_url = "127.0.0.1"
        self._logger = logger

    def _get_list_resources(
            self, resource_url, service_type, session, viminfo,
            vimid, content_key):
        service = {'service_type': service_type,
                   'interface': 'public',
                   'region_id': viminfo['openstack_region_id']
                       if viminfo.get('openstack_region_id')
                       else viminfo['cloud_region_id']}

        self._logger.info("making request with URI:%s" % resource_url)
        resp = session.get(resource_url, endpoint_filter=service)
        self._logger.info("request returns with status %s" % resp.status_code)
        if resp.status_code == status.HTTP_200_OK:
            self._logger.debug("with content:%s" % resp.json())
            content = resp.json()
            return content.get(content_key)
        return  # failed to discover resources

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
            if e.http_status == status.HTTP_403_FORBIDDEN:
                ### get the tenant information from the token response
                try:
                    ### get tenant info from the session
                    tmp_auth_state = VimDriverUtils.get_auth_state(session)
                    tmp_auth_info = json.loads(tmp_auth_state)
                    tmp_auth_data = tmp_auth_info['body']
                    tenant = tmp_auth_data['token']['project']
                    tenant_info = {
                        'tenant-id': tenant['id'],
                        'tenant-name': tenant['name'],
                    }

                    self._update_resoure(
                        cloud_owner, cloud_region_id, tenant['id'],
                        tenant_info, "tenant")

                except Exception as ex:
                    self._logger.error(traceback.format_exc())
            else:
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

                if flavor.get('links') and len(flavor['links']) > 0:
                    flavor_info['flavor-selflink'] = flavor['links'][0]['href'] or 'http://0.0.0.0'
                else:
                    flavor_info['flavor-selflink'] = 'http://0.0.0.0'

                # add hpa capabilities
                if (flavor['name'].find('onap.') == 0):
                    req_resouce = "/flavors/%s/os-extra_specs" % flavor['id']
                    extraResp = self._get_list_resources(req_resouce, "compute", session, viminfo, vimid, "extra_specs")

                    hpa_capabilities = self._get_hpa_capabilities(flavor, extraResp, viminfo)
                    flavor_info['hpa-capabilities'] = {'hpa-capability': hpa_capabilities}

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

    def _get_hpa_capabilities(self, flavor, extra_specs, viminfo):
        hpa_caps = []

        # Basic capabilties
        caps_dict = self._get_hpa_basic_capabilities(flavor)
        if len(caps_dict) > 0:
            self._logger.debug("basic_capabilities_info: %s" % caps_dict)
            hpa_caps.append(caps_dict)

        # cpupining capabilities
        caps_dict = self._get_cpupining_capabilities(extra_specs)
        if len(caps_dict) > 0:
            self._logger.debug("cpupining_capabilities_info: %s" % caps_dict)
            hpa_caps.append(caps_dict)

        # cputopology capabilities
        caps_dict = self._get_cputopology_capabilities(extra_specs)
        if len(caps_dict) > 0:
            self._logger.debug("cputopology_capabilities_info: %s" % caps_dict)
            hpa_caps.append(caps_dict)

        # hugepages capabilities
        caps_dict = self._get_hugepages_capabilities(extra_specs)
        if len(caps_dict) > 0:
            self._logger.debug("hugepages_capabilities_info: %s" % caps_dict)
            hpa_caps.append(caps_dict)

        # numa capabilities
        caps_dict = self._get_numa_capabilities(extra_specs)
        if len(caps_dict) > 0:
            self._logger.debug("numa_capabilities_info: %s" % caps_dict)
            hpa_caps.append(caps_dict)

        # storage capabilities
        caps_dict = self._get_storage_capabilities(flavor)
        if len(caps_dict) > 0:
            self._logger.debug("storage_capabilities_info: %s" % caps_dict)
            hpa_caps.append(caps_dict)

        # CPU instruction set extension capabilities
        caps_dict = self._get_instruction_set_capabilities(extra_specs)
        if len(caps_dict) > 0:
            self._logger.debug("instruction_set_capabilities_info: %s" % caps_dict)
            hpa_caps.append(caps_dict)

        # PCI passthrough capabilities
        caps_dict = self._get_pci_passthrough_capabilities(extra_specs)
        if len(caps_dict) > 0:
            self._logger.debug("pci_passthrough_capabilities_info: %s" % caps_dict)
            hpa_caps.append(caps_dict)

        # ovsdpdk capabilities
        caps_dict = self._get_ovsdpdk_capabilities(extra_specs, viminfo)
        if len(caps_dict) > 0:
            self._logger.debug("ovsdpdk_capabilities_info: %s" % caps_dict)
            hpa_caps.append(caps_dict)

        return hpa_caps

    def _get_hpa_basic_capabilities(self, flavor):
        basic_capability = {}
        feature_uuid = uuid.uuid4()

        basic_capability['hpa-capability-id'] = str(feature_uuid)
        basic_capability['hpa-feature'] = 'basicCapabilities'
        basic_capability['architecture'] = 'generic'
        basic_capability['hpa-version'] = 'v1'

        basic_capability['hpa-feature-attributes'] = []
        basic_capability['hpa-feature-attributes'].append({'hpa-attribute-key': 'numVirtualCpu',
                                               'hpa-attribute-value':
                                                   '{{\"value\":\"{0}\"}}'.format(flavor['vcpus'])
                                                           })
        basic_capability['hpa-feature-attributes'].append({'hpa-attribute-key':'virtualMemSize',
                                               'hpa-attribute-value':
                                                   '{{\"value\":\"{0}\",\"unit\":\"{1}\"}}'.format(flavor['ram'],"MB")
                                                           })

        return basic_capability

    def _get_cpupining_capabilities(self, extra_specs):
        cpupining_capability = {}
        feature_uuid = uuid.uuid4()

        if extra_specs.has_key('hw:cpu_policy') or extra_specs.has_key('hw:cpu_thread_policy'):
            cpupining_capability['hpa-capability-id'] = str(feature_uuid)
            cpupining_capability['hpa-feature'] = 'cpuPinning'
            cpupining_capability['architecture'] = 'generic'
            cpupining_capability['hpa-version'] = 'v1'

            cpupining_capability['hpa-feature-attributes'] = []
            if extra_specs.has_key('hw:cpu_thread_policy'):
                cpupining_capability['hpa-feature-attributes'].append({'hpa-attribute-key': 'logicalCpuThreadPinningPolicy',
                                                           'hpa-attribute-value':
                                                               '{{\"value\":\"{0}\"}}'.format(extra_specs['hw:cpu_thread_policy'])
                                                                       })
            if extra_specs.has_key('hw:cpu_policy'):
                cpupining_capability['hpa-feature-attributes'].append({'hpa-attribute-key':'logicalCpuPinningPolicy',
                                                           'hpa-attribute-value':
                                                               '{{\"value\":\"{0}\"}}'.format(extra_specs['hw:cpu_policy'])
                                                                       })

        return cpupining_capability

    def _get_cputopology_capabilities(self, extra_specs):
        cputopology_capability = {}
        feature_uuid = uuid.uuid4()

        if extra_specs.has_key('hw:cpu_sockets') or extra_specs.has_key('hw:cpu_cores') or extra_specs.has_key('hw:cpu_threads'):
            cputopology_capability['hpa-capability-id'] = str(feature_uuid)
            cputopology_capability['hpa-feature'] = 'cpuTopology'
            cputopology_capability['architecture'] = 'generic'
            cputopology_capability['hpa-version'] = 'v1'

            cputopology_capability['hpa-feature-attributes'] = []
            if extra_specs.has_key('hw:cpu_sockets'):
                cputopology_capability['hpa-feature-attributes'].append({'hpa-attribute-key': 'numCpuSockets',
                                                             'hpa-attribute-value':
                                                               '{{\"value\":\"{0}\"}}'.format(extra_specs['hw:cpu_sockets'])
                                                                         })
            if extra_specs.has_key('hw:cpu_cores'):
                cputopology_capability['hpa-feature-attributes'].append({'hpa-attribute-key': 'numCpuCores',
                                                             'hpa-attribute-value':
                                                               '{{\"value\":\"{0}\"}}'.format(extra_specs['hw:cpu_cores'])
                                                                         })
            if extra_specs.has_key('hw:cpu_threads'):
                cputopology_capability['hpa-feature-attributes'].append({'hpa-attribute-key': 'numCpuThreads',
                                                             'hpa-attribute-value':
                                                               '{{\"value\":\"{0}\"}}'.format(extra_specs['hw:cpu_threads'])
                                                                         })

        return cputopology_capability

    def _get_hugepages_capabilities(self, extra_specs):
        hugepages_capability = {}
        feature_uuid = uuid.uuid4()

        if extra_specs.has_key('hw:mem_page_size'):
            hugepages_capability['hpa-capability-id'] = str(feature_uuid)
            hugepages_capability['hpa-feature'] = 'hugePages'
            hugepages_capability['architecture'] = 'generic'
            hugepages_capability['hpa-version'] = 'v1'

            hugepages_capability['hpa-feature-attributes'] = []
            if extra_specs['hw:mem_page_size'] == 'large':
                hugepages_capability['hpa-feature-attributes'].append({'hpa-attribute-key': 'memoryPageSize',
                                                           'hpa-attribute-value':
                                                   '{{\"value\":\"{0}\",\"unit\":\"{1}\"}}'.format(2,"MB")
                                                                       })
            elif extra_specs['hw:mem_page_size'] == 'small':
                hugepages_capability['hpa-feature-attributes'].append({'hpa-attribute-key': 'memoryPageSize',
                                                           'hpa-attribute-value':
                                                   '{{\"value\":\"{0}\",\"unit\":\"{1}\"}}'.format(4,"KB")
                                                                       })
            elif extra_specs['hw:mem_page_size'] == 'any':
                self._logger.info("Currently HPA feature memoryPageSize did not support 'any' page!!")
            else :
                hugepages_capability['hpa-feature-attributes'].append({'hpa-attribute-key': 'memoryPageSize',
                                                           'hpa-attribute-value':
                                                   '{{\"value\":\"{0}\",\"unit\":\"{1}\"}}'.format(extra_specs['hw:mem_page_size'],"KB")
                                                                       })
        return hugepages_capability

    def _get_numa_capabilities(self, extra_specs):
        numa_capability = {}
        feature_uuid = uuid.uuid4()

        if extra_specs.has_key('hw:numa_nodes'):
            numa_capability['hpa-capability-id'] = str(feature_uuid)
            numa_capability['hpa-feature'] = 'numa'
            numa_capability['architecture'] = 'generic'
            numa_capability['hpa-version'] = 'v1'

            numa_capability['hpa-feature-attributes'] = []
            numa_capability['hpa-feature-attributes'].append({'hpa-attribute-key': 'numaNodes',
                                                  'hpa-attribute-value':
                                                      '{{\"value\":\"{0}\"}}'.format(extra_specs['hw:numa_nodes'] or 0)
                                                              })

            for num in range(0, int(extra_specs['hw:numa_nodes'])):
                numa_cpu_node = "hw:numa_cpus.%s" % num
                numa_mem_node = "hw:numa_mem.%s" % num
                numacpu_key = "numaCpu-%s" % num
                numamem_key = "numaMem-%s" % num

                if extra_specs.has_key(numa_cpu_node) and extra_specs.has_key(numa_mem_node):
                    numa_capability['hpa-feature-attributes'].append({'hpa-attribute-key': numacpu_key,
                                                          'hpa-attribute-value':
                                                               '{{\"value\":\"{0}\"}}'.format(extra_specs[numa_cpu_node])
                                                                      })
                    numa_capability['hpa-feature-attributes'].append({'hpa-attribute-key': numamem_key,
                                                          'hpa-attribute-value':
                                                   '{{\"value\":\"{0}\",\"unit\":\"{1}\"}}'.format(extra_specs[numa_mem_node],"MB")
                                                                      })

        return numa_capability

    def _get_storage_capabilities(self, flavor):
        storage_capability = {}
        feature_uuid = uuid.uuid4()

        storage_capability['hpa-capability-id'] = str(feature_uuid)
        storage_capability['hpa-feature'] = 'localStorage'
        storage_capability['architecture'] = 'generic'
        storage_capability['hpa-version'] = 'v1'

        storage_capability['hpa-feature-attributes'] = []
        storage_capability['hpa-feature-attributes'].append({'hpa-attribute-key': 'diskSize',
                                                       'hpa-attribute-value':
                                                   '{{\"value\":\"{0}\",\"unit\":\"{1}\"}}'.format(flavor['disk'] or 0,"GB")
                                                             })
        storage_capability['hpa-feature-attributes'].append({'hpa-attribute-key': 'swapMemSize',
                                                       'hpa-attribute-value':
                                                   '{{\"value\":\"{0}\",\"unit\":\"{1}\"}}'.format(flavor['swap'] or 0,"MB")
                                                             })
        storage_capability['hpa-feature-attributes'].append({'hpa-attribute-key': 'ephemeralDiskSize',
                                                       'hpa-attribute-value':
                                                   '{{\"value\":\"{0}\",\"unit\":\"{1}\"}}'.format(flavor['OS-FLV-EXT-DATA:ephemeral'] or 0,"GB")
                                                             })
        return storage_capability

    def _get_instruction_set_capabilities(self, extra_specs):
        instruction_capability = {}
        feature_uuid = uuid.uuid4()

        if extra_specs.has_key('hw:capabilities:cpu_info:features'):
            instruction_capability['hpa-capability-id'] = str(feature_uuid)
            instruction_capability['hpa-feature'] = 'instructionSetExtensions'
            instruction_capability['architecture'] = 'Intel64'
            instruction_capability['hpa-version'] = 'v1'

            instruction_capability['hpa-feature-attributes'] = []
            instruction_capability['hpa-feature-attributes'].append({'hpa-attribute-key': 'instructionSetExtensions',
                                                       'hpa-attribute-value':
                                                      '{{\"value\":\"{0}\"}}'.format(extra_specs['hw:capabilities:cpu_info:features'])
                                                                     })
        return instruction_capability

    def _get_pci_passthrough_capabilities(self, extra_specs):
        pci_passthrough_capability = {}
        feature_uuid = uuid.uuid4()

        if extra_specs.has_key('pci_passthrough:alias'):
            value1 = extra_specs['pci_passthrough:alias'].split(':')
            value2 = value1[0].split('-')

            pci_passthrough_capability['hpa-capability-id'] = str(feature_uuid)
            pci_passthrough_capability['hpa-feature'] = 'pciePassthrough'
            pci_passthrough_capability['architecture'] = str(value2[2])
            pci_passthrough_capability['hpa-version'] = 'v1'


            pci_passthrough_capability['hpa-feature-attributes'] = []
            pci_passthrough_capability['hpa-feature-attributes'].append({'hpa-attribute-key': 'pciCount',
                                                       'hpa-attribute-value':
                                                      '{{\"value\":\"{0}\"}}'.format(value1[1])
                                                                     })
            pci_passthrough_capability['hpa-feature-attributes'].append({'hpa-attribute-key': 'pciVendorId',
                                                       'hpa-attribute-value':
                                                      '{{\"value\":\"{0}\"}}'.format(value2[3])
                                                                     })
            pci_passthrough_capability['hpa-feature-attributes'].append({'hpa-attribute-key': 'pciDeviceId',
                                                       'hpa-attribute-value':
                                                      '{{\"value\":\"{0}\"}}'.format(value2[4])
                                                                     })

        return pci_passthrough_capability

    def _get_ovsdpdk_capabilities(self, extra_specs, viminfo):
        ovsdpdk_capability = {}
        feature_uuid = uuid.uuid4()

        cloud_extra_info_str = viminfo.get('cloud_extra_info')
        if not isinstance(cloud_extra_info_str, dict):
            try:
                cloud_extra_info_str = json.loads(cloud_extra_info_str)
            except Exception as ex:
                logger.error("Can not convert cloud extra info %s %s" % (
                             str(ex), cloud_extra_info_str))
                return {}
        if cloud_extra_info_str :
            cloud_dpdk_info = cloud_extra_info_str.get("ovsDpdk")
            if cloud_dpdk_info :
                ovsdpdk_capability['hpa-capability-id'] = str(feature_uuid)
                ovsdpdk_capability['hpa-feature'] = 'ovsDpdk'
                ovsdpdk_capability['architecture'] = 'Intel64'
                ovsdpdk_capability['hpa-version'] = 'v1'

                ovsdpdk_capability['hpa-feature-attributes'] = [
                    {
                        'hpa-attribute-key': str(cloud_dpdk_info.get("libname")),
                        'hpa-attribute-value': '{{\"value\":\"{0}\"}}'.format(cloud_dpdk_info.get("libversion"))
                    },]

        return ovsdpdk_capability

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
                               'region_id': viminfo['openstack_region_id']
                               if viminfo.get('openstack_region_id')
                               else viminfo['cloud_region_id']
                               }

                    self._logger.info("making request with URI:%s" % req_resource)
                    resp = session.get(req_resource, endpoint_filter=service)
                    self._logger.info("request returns with status %s" % resp.status_code)
                    if resp.status_code == status.HTTP_200_OK:
                        self._logger.debug("with content:%s" % resp.json())
                        pass
                    content = resp.json()

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
                                   'region_id': viminfo['openstack_region_id']
                                   if viminfo.get('openstack_region_id')
                                   else viminfo['cloud_region_id']
                                   }

                        self._logger.info("making request with URI:%s" % req_resource)
                        resp = session.get(req_resource, endpoint_filter=service)
                        self._logger.info("request returns with status %s" % resp.status_code)
                        if resp.status_code == status.HTTP_200_OK:
                            self._logger.debug("with content:%s" % resp.json())
                            pass
                        content = resp.json()
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
                                    self.aai_base_url, cloud_owner,
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
                    viminfo['identity-url'] = self.proxy_prefix + "/%s/identity/v2.0" % vimid \
                        if self.proxy_prefix[-3:] == "/v0" else \
                        self.proxy_prefix + "/%s/%s/identity/v2.0" % extsys.decode_vim_id(vimid)

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
        self._logger.info("registration with vimid: %s" % vimid)
        self._logger.debug("with data: %s" % request.data)

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

            # prepare request resource to vim instance
            # get token:
            viminfo = VimDriverUtils.get_vim_info(vimid)
            if not viminfo:
                raise VimDriverNewtonException(
                    "There is no cloud-region with {cloud-owner}_{cloud-region-id}=%s in AAI" % vimid)

            cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)

            #get the resource first
            resource_url = ("/cloud-infrastructure/cloud-regions/"
                     "cloud-region/%(cloud_owner)s/%(cloud_region_id)s?depth=all"
                     % {
                         "cloud_owner": cloud_owner,
                         "cloud_region_id": cloud_region_id,
                     })

            # get cloud-region
            retcode, content, status_code = \
                restcall.req_to_aai(resource_url, "GET")

            # add resource-version
            if retcode == 0 and content:
                cloudregiondata = json.JSONDecoder().decode(content)

            # step 1. remove all tenants
            tenants = cloudregiondata.get("tenants", None)
            for tenant in tenants.get("tenant", []) if tenants else []:
                resource_url = ("/cloud-infrastructure/cloud-regions/"
                     "cloud-region/%(cloud_owner)s/%(cloud_region_id)s/"
                     "%(resource_type)ss/%(resource_type)s/%(resoure_id)s/"
                     "?resource-version=%(resource-version)s"
                     % {
                         "cloud_owner": cloud_owner,
                         "cloud_region_id": cloud_region_id,
                         "resource_type": "tenant",
                         "resoure_id": tenant["tenant-id"],
                         "resource-version": tenant["resource-version"]
                     })
                # remove tenant
                retcode, content, status_code = \
                    restcall.req_to_aai(resource_url, "DELETE")

            # remove all flavors
            flavors = cloudregiondata.get("flavors", None)
            for flavor in flavors.get("flavor", []) if flavors else []:
                # iterate hpa-capabilities
                hpa_capabilities = flavor.get("hpa-capabilities", None)
                for hpa_capability in hpa_capabilities.get("hpa-capability", []) if hpa_capabilities else []:
                    resource_url = ("/cloud-infrastructure/cloud-regions/"
                                    "cloud-region/%(cloud_owner)s/%(cloud_region_id)s/"
                                    "%(resource_type)ss/%(resource_type)s/%(resoure_id)s/"
                                    "hpa-capabilities/hpa-capability/%(hpa-capability-id)s/"
                                    "?resource-version=%(resource-version)s"
                                    % {
                                        "cloud_owner": cloud_owner,
                                        "cloud_region_id": cloud_region_id,
                                        "resource_type": "flavor",
                                        "resoure_id": flavor["flavor-id"],
                                        "hpa-capability-id": hpa_capability["hpa-capability-id"],
                                        "resource-version": hpa_capability["resource-version"]
                                    })
                    # remove hpa-capability
                    retcode, content, status_code = \
                        restcall.req_to_aai(resource_url, "DELETE")

                # remove flavor
                resource_url = ("/cloud-infrastructure/cloud-regions/"
                     "cloud-region/%(cloud_owner)s/%(cloud_region_id)s/"
                     "%(resource_type)ss/%(resource_type)s/%(resoure_id)s/"
                     "?resource-version=%(resource-version)s"
                     % {
                         "cloud_owner": cloud_owner,
                         "cloud_region_id": cloud_region_id,
                         "resource_type": "flavor",
                         "resoure_id": flavor["flavor-id"],
                         "resource-version": flavor["resource-version"]
                     })

                retcode, content, status_code = \
                    restcall.req_to_aai(resource_url, "DELETE")

            # remove all images
            images = cloudregiondata.get("images", None)
            for image in images.get("image", []) if images else []:
                resource_url = ("/cloud-infrastructure/cloud-regions/"
                     "cloud-region/%(cloud_owner)s/%(cloud_region_id)s/"
                     "%(resource_type)ss/%(resource_type)s/%(resoure_id)s/"
                     "?resource-version=%(resource-version)s"
                     % {
                         "cloud_owner": cloud_owner,
                         "cloud_region_id": cloud_region_id,
                         "resource_type": "image",
                         "resoure_id": image["image-id"],
                         "resource-version": image["resource-version"]
                     })
                # remove image
                retcode, content, status_code = \
                    restcall.req_to_aai(resource_url, "DELETE")

            # remove all az

            # remove all vg

            # remove all snapshots
            snapshots = cloudregiondata.get("snapshots", None)
            for snapshot in snapshots.get("snapshot", []) if snapshots else []:
                resource_url = ("/cloud-infrastructure/cloud-regions/"
                     "cloud-region/%(cloud_owner)s/%(cloud_region_id)s/"
                     "%(resource_type)ss/%(resource_type)s/%(resoure_id)s/"
                     "?resource-version=%(resource-version)s"
                     % {
                         "cloud_owner": cloud_owner,
                         "cloud_region_id": cloud_region_id,
                         "resource_type": "snapshot",
                         "resoure_id": snapshot["snapshot-id"],
                         "resource-version": snapshot["resource-version"]
                     })
                # remove snapshot
                retcode, content, status_code = \
                    restcall.req_to_aai(resource_url, "DELETE")

            # remove all server groups

            # remove all pservers

            # remove cloud region itself
            resource_url = ("/cloud-infrastructure/cloud-regions/"
                 "cloud-region/%(cloud_owner)s/%(cloud_region_id)s"
                 "?resource-version=%(resource-version)s"
                 % {
                     "cloud_owner": cloud_owner,
                     "cloud_region_id": cloud_region_id,
                     "resource-version": cloudregiondata["resource-version"]
                 })
            # remove cloud region
            retcode, content, status_code = \
                restcall.req_to_aai(resource_url, "DELETE")

            #ret_code = VimDriverUtils.delete_vim_info(vimid)
            return Response(status=status.HTTP_204_NO_CONTENT if retcode==0 else status.HTTP_500_INTERNAL_SERVER_ERROR)
        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
