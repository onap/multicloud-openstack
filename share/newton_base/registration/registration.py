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
from common.msapi.helper import MultiCloudThreadHelper
from common.msapi.helper import MultiCloudAAIHelper
from common.utils import restcall
from newton_base.util import VimDriverUtils
from django.conf import settings

logger = logging.getLogger(__name__)


class Registry(APIView):

    def __init__(self):
        # logger.debug("Registry __init__: %s" % traceback.format_exc())
        if not hasattr(self, "_logger"):
            self._logger = logger

        if not hasattr(self, "register_thread"):
            # dedicate thread to offload vim registration process
            self.register_thread = MultiCloudThreadHelper("vimupdater")

        if not hasattr(self, "register_helper") or not self.register_helper:
            if not hasattr(self, "proxy_prefix"):
                self.proxy_prefix = "multicloud"
            if not hasattr(self, "AAI_BASE_URL"):
                self.AAI_BASE_URL = "127.0.0.1"
            self.register_helper = RegistryHelper(
                self.proxy_prefix or "multicloud",
                self.AAI_BASE_URL or "127.0.0.1")

    def post(self, request, vimid=""):
        self._logger.info("registration with vimid: %s" % vimid)
        self._logger.debug("with data: %s" % request.data)

        try:
            # Get the specified tenant id
            specified_project_idorname = request.META.get("Project", None)

            # compose the one time backlog item
            backlog_item = {
                "id": vimid,
                "worker": self.register_helper.registryV0,
                "payload": (vimid, specified_project_idorname),
                "repeat": 0,
                "status": (1,
                           "The registration is on progress")
            }
            self.register_thread.add(backlog_item)
            if 0 == self.register_thread.state():
                self.register_thread.start()

            return Response(status=status.HTTP_202_ACCEPTED)

        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s"
                               % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return Response(
                data={'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, vimid):
        try:
            backlog_item = self.register_thread.get(vimid)
            if backlog_item:
                return Response(
                    data={'status': backlog_item.get(
                        "status", "Status not available, vimid: %s" % vimid)},
                    status=status.HTTP_200_OK)
            else:
                return Response(
                    data={
                        'error': "Registration process for "
                                 "Cloud Region not found: %s"
                                 % vimid
                    },
                    status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return Response(
                data={'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, vimid=""):
        self._logger.debug("Registration--delete::data> %s" % request.data)
        self._logger.debug("Registration--delete::vimid > %s"% vimid)
        try:

            # compose the one time backlog item
            backlog_item = {
                "id": vimid,
                "worker": self.register_helper.unregistryV0,
                "payload": (vimid),
                "repeat": 0,
                "status": (1, "The de-registration is on process")
            }
            self.register_thread.add(backlog_item)
            if 0 == self.register_thread.state():
                self.register_thread.start()

            return Response(
                status=status.HTTP_204_NO_CONTENT
            )
        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s"
                               % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class RegistryHelper(MultiCloudAAIHelper):
    '''
    Helper code to discover and register a cloud region's resource
    '''

    def __init__(self, multicloud_prefix, aai_base_url):
        # logger.debug("RegistryHelper __init__: %s" % traceback.format_exc())
        self.proxy_prefix = multicloud_prefix
        self.aai_base_url = aai_base_url
        self._logger = logger
        super(RegistryHelper, self).__init__(multicloud_prefix, aai_base_url)

    def registryV1(self, cloud_owner, cloud_region_id):
        # cloud_owner = payload.get("cloud-owner", None)
        # cloud_region_id = payload.get("cloud-region-id", None)
        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return self.registryV0(vimid)

    def registryV0(self, vimid, project_idorname=None):
        # populate proxy identity url
        self._update_proxy_identity_endpoint(vimid)

        # prepare request resource to vim instance
        # get token:
        viminfo = VimDriverUtils.get_vim_info(vimid)
        sess = None
        if not viminfo:
            return (
                10,
                "Cloud Region not found in AAI: %s" % vimid
            )
        if project_idorname:
            try:
                # check if specified with tenant id
                sess = VimDriverUtils.get_session(
                    viminfo, tenant_name=None,
                    tenant_id=project_idorname
                )
            except Exception as e:
                pass

            if not sess:
                try:
                    # check if specified with tenant name
                    sess = VimDriverUtils.get_session(
                        viminfo, tenant_name=project_idorname,
                        tenant_id=None
                    )
                except Exception as e:
                    pass

        if not sess:
            # set the default tenant since there is no tenant info in the VIM yet
            sess = VimDriverUtils.get_session(
                viminfo, tenant_name=viminfo.get('tenant', None))

        # step 1. discover all projects and populate into AAI
        retcode, status = self._discover_tenants(vimid, sess, viminfo)
        # if 0 != retcode:
        #     return (
        #         retcode, status
        #     )

        # discover all flavors
        retcode, status = self._discover_flavors(vimid, sess, viminfo)
        # if 0 != retcode:
        #     return (
        #         retcode, status
        #     )

        # discover all images
        retcode, status = self._discover_images(vimid, sess, viminfo)
        # if 0 != retcode:
        #     return (
        #         retcode, status
        #     )

        # discover all az
        retcode, status = self._discover_availability_zones(vimid, sess, viminfo)
        # if 0 != retcode:
        #     return (
        #         retcode, status
        #     )

        # discover all vg
        #self._discover_volumegroups(vimid, sess, viminfo)
        # if 0 != retcode:
        #     return (
        #         retcode, status
        #     )

        # discover all snapshots
        #self._discover_snapshots(vimid, sess, viminfo)
        # if 0 != retcode:
        #     return retcode, status

        # discover all server groups
        #self.discover_servergroups(request, vimid, sess, viminfo)
        # if 0 != retcode:
        #     return retcode, status

        # discover all pservers
        #self._discover_pservers(vimid, sess, viminfo)
        # if 0 != retcode:
        #     return retcode, status

        return (
            0,
            "Registration finished for Cloud Region: %s" % vimid
        )

    def unregistryV1(self, cloud_owner, cloud_region_id):
        # cloud_owner = payload.get("cloud-owner", None)
        # cloud_region_id = payload.get("cloud-region-id", None)
        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return self.unregistryV0(vimid)

    def unregistryV0(self, vimid):
        # prepare request resource to vim instance
        # get token:
        viminfo = VimDriverUtils.get_vim_info(vimid)
        if not viminfo:
            return (
                10,
                "Cloud Region not found:" % vimid
            )

        cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)

        # get the resource first
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
        cloudregiondata = {}
        if retcode == 0 and content:
            cloudregiondata = json.JSONDecoder().decode(content)
        else:
            return (
                10,
                "Cloud Region not found: %s, %s" % (cloud_owner, cloud_region_id)
            )

        # step 1. remove all tenants
        tenants = cloudregiondata.get("tenants", None)
        for tenant in tenants.get("tenant", []) if tenants else []:
            # common prefix
            aai_cloud_region = \
                "/cloud-infrastructure/cloud-regions/cloud-region/%s/%s/tenants/tenant/%s" \
                % (cloud_owner, cloud_region_id, tenant['tenant-id'])

            # remove all vservers
            try:
                # get list of vservers
                vservers = tenant.get('vservers', {}).get('vserver', [])
                for vserver in vservers:
                    try:
                        # iterate vport, except will be raised if no l-interface exist
                        for vport in vserver['l-interfaces']['l-interface']:
                            # delete vport
                            vport_delete_url =\
                                aai_cloud_region + \
                                "/vservers/vserver/%s/l-interfaces/l-interface/%s?resource-version=%s" \
                                % (vserver['vserver-id'], vport['interface-name'],
                                   vport['resource-version'])
                            restcall.req_to_aai(vport_delete_url, "DELETE")
                    except Exception as e:
                        pass

                    try:
                        # delete vserver
                        vserver_delete_url =\
                            aai_cloud_region +\
                            "/vservers/vserver/%s?resource-version=%s" \
                            % (vserver['vserver-id'],
                               vserver['resource-version'])
                        restcall.req_to_aai(vserver_delete_url, "DELETE")
                    except Exception as e:
                        continue

            except Exception:
                self._logger.error(traceback.format_exc())
                pass

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
            for hpa_capability in hpa_capabilities.get("hpa-capability", [])\
                    if hpa_capabilities else []:
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

        return retcode, content

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
            return 0, "succeed"
        except VimDriverNewtonException as e:
            self._logger.error(
                "VimDriverNewtonException: status:%s, response:%s"
                % (e.http_status, e.content))
            return (
                e.http_status, e.content
            )
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

                    return 0, "succeed"

                except Exception as ex:
                    self._logger.error(traceback.format_exc())
                    return (
                        11,
                        ex.message
                    )
            else:
                self._logger.error(
                    "HttpError: status:%s, response:%s"
                    % (e.http_status, e.response.json()))
                return (
                    e.http_status, e.response.json()
                )
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return (
                11,
                e.message
            )

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
                    flavor_info['flavor-selflink'] =\
                        flavor['links'][0]['href'] or 'http://0.0.0.0'
                else:
                    flavor_info['flavor-selflink'] = 'http://0.0.0.0'

                # add hpa capabilities
                if (flavor['name'].find('onap.') == 0):
                    req_resouce = "/flavors/%s/os-extra_specs" % flavor['id']
                    extraResp = self._get_list_resources(
                        req_resouce, "compute", session,
                        viminfo, vimid, "extra_specs")

                    hpa_capabilities =\
                        self._get_hpa_capabilities(flavor, extraResp, viminfo)
                    flavor_info['hpa-capabilities'] = \
                        {'hpa-capability': hpa_capabilities}

                retcode, content = self._update_resoure(
                    cloud_owner, cloud_region_id, flavor['id'],
                    flavor_info, "flavor")

            return (0, "succeed")
        except VimDriverNewtonException as e:
            self._logger.error(
                "VimDriverNewtonException: status:%s, response:%s" %
                (e.http_status, e.content))
            return (
                e.http_status, e.content
            )
        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s" %
                               (e.http_status, e.response.json()))
            return (
                e.http_status, e.response.json()
            )
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return (
                11, e.message
            )

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

        # SRIOV-NIC capabilities
        caps_dict = self._get_sriov_nic_capabilities(extra_specs)
        if len(caps_dict) > 0:
            self._logger.debug("sriov_nic_capabilities_info: %s" % caps_dict)
            hpa_caps.append(caps_dict)

        # ovsdpdk capabilities
        caps_dict = self._get_ovsdpdk_capabilities(extra_specs, viminfo)
        if len(caps_dict) > 0:
            self._logger.debug("ovsdpdk_capabilities_info: %s" % caps_dict)
            hpa_caps.append(caps_dict)

        logger.debug("hpa_caps:%s" % hpa_caps)
        return hpa_caps

    def _get_hpa_basic_capabilities(self, flavor):
        basic_capability = {}
        feature_uuid = uuid.uuid4()

        try:
            basic_capability['hpa-capability-id'] = str(feature_uuid)
            basic_capability['hpa-feature'] = 'basicCapabilities'
            basic_capability['architecture'] = 'generic'
            basic_capability['hpa-version'] = 'v1'

            basic_capability['hpa-feature-attributes'] = []
            basic_capability['hpa-feature-attributes'].append(
                {'hpa-attribute-key': 'numVirtualCpu',
                 'hpa-attribute-value':
                     '{{\"value\":\"{0}\"}}'.format(flavor['vcpus'])
                 })
            basic_capability['hpa-feature-attributes'].append(
                {'hpa-attribute-key':'virtualMemSize',
                 'hpa-attribute-value':
                     '{{\"value\":\"{0}\",\"unit\":\"{1}\"}}'.format(flavor['ram'],"MB")
                 })
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return (
                11, e.message
            )

        return basic_capability

    def _get_cpupining_capabilities(self, extra_specs):
        cpupining_capability = {}
        feature_uuid = uuid.uuid4()

        try:
            if extra_specs.has_key('hw:cpu_policy')\
                    or extra_specs.has_key('hw:cpu_thread_policy'):
                cpupining_capability['hpa-capability-id'] = str(feature_uuid)
                cpupining_capability['hpa-feature'] = 'cpuPinning'
                cpupining_capability['architecture'] = 'generic'
                cpupining_capability['hpa-version'] = 'v1'

                cpupining_capability['hpa-feature-attributes'] = []
                if extra_specs.has_key('hw:cpu_thread_policy'):
                    cpupining_capability['hpa-feature-attributes'].append(
                        {'hpa-attribute-key': 'logicalCpuThreadPinningPolicy',
                         'hpa-attribute-value':
                             '{{\"value\":\"{0}\"}}'.format(
                                 extra_specs['hw:cpu_thread_policy'])
                         })
                if extra_specs.has_key('hw:cpu_policy'):
                    cpupining_capability['hpa-feature-attributes'].append(
                        {'hpa-attribute-key':'logicalCpuPinningPolicy',
                         'hpa-attribute-value':
                             '{{\"value\":\"{0}\"}}'.format(
                                 extra_specs['hw:cpu_policy'])
                         })
        except Exception:
            self._logger.error(traceback.format_exc())

        return cpupining_capability

    def _get_cputopology_capabilities(self, extra_specs):
        cputopology_capability = {}
        feature_uuid = uuid.uuid4()

        try:
            if extra_specs.has_key('hw:cpu_sockets')\
                    or extra_specs.has_key('hw:cpu_cores')\
                    or extra_specs.has_key('hw:cpu_threads'):
                cputopology_capability['hpa-capability-id'] = str(feature_uuid)
                cputopology_capability['hpa-feature'] = 'cpuTopology'
                cputopology_capability['architecture'] = 'generic'
                cputopology_capability['hpa-version'] = 'v1'

                cputopology_capability['hpa-feature-attributes'] = []
                if extra_specs.has_key('hw:cpu_sockets'):
                    cputopology_capability['hpa-feature-attributes'].append(
                        {'hpa-attribute-key': 'numCpuSockets',
                         'hpa-attribute-value':
                             '{{\"value\":\"{0}\"}}'.format(extra_specs['hw:cpu_sockets'])
                         })
                if extra_specs.has_key('hw:cpu_cores'):
                    cputopology_capability['hpa-feature-attributes'].append(
                        {'hpa-attribute-key': 'numCpuCores',
                         'hpa-attribute-value':
                             '{{\"value\":\"{0}\"}}'.format(extra_specs['hw:cpu_cores'])
                         })
                if extra_specs.has_key('hw:cpu_threads'):
                    cputopology_capability['hpa-feature-attributes'].append(
                        {'hpa-attribute-key': 'numCpuThreads',
                         'hpa-attribute-value':
                             '{{\"value\":\"{0}\"}}'.format(extra_specs['hw:cpu_threads'])
                         })
        except Exception:
            self._logger.error(traceback.format_exc())

        return cputopology_capability

    def _get_hugepages_capabilities(self, extra_specs):
        hugepages_capability = {}
        feature_uuid = uuid.uuid4()

        try:
            if extra_specs.has_key('hw:mem_page_size'):
                hugepages_capability['hpa-capability-id'] = str(feature_uuid)
                hugepages_capability['hpa-feature'] = 'hugePages'
                hugepages_capability['architecture'] = 'generic'
                hugepages_capability['hpa-version'] = 'v1'

                hugepages_capability['hpa-feature-attributes'] = []
                if extra_specs['hw:mem_page_size'] == 'large':
                    hugepages_capability['hpa-feature-attributes'].append(
                        {'hpa-attribute-key': 'memoryPageSize',
                         'hpa-attribute-value':
                             '{{\"value\":\"{0}\",\"unit\":\"{1}\"}}'.format(2,"MB")
                         })
                elif extra_specs['hw:mem_page_size'] == 'small':
                    hugepages_capability['hpa-feature-attributes'].append(
                        {'hpa-attribute-key': 'memoryPageSize',
                         'hpa-attribute-value':
                             '{{\"value\":\"{0}\",\"unit\":\"{1}\"}}'.format(4,"KB")
                         })
                elif extra_specs['hw:mem_page_size'] == 'any':
                    self._logger.info("Currently HPA feature memoryPageSize did not support 'any' page!!")
                else :
                    hugepages_capability['hpa-feature-attributes'].append(
                        {'hpa-attribute-key': 'memoryPageSize',
                         'hpa-attribute-value':
                             '{{\"value\":\"{0}\",\"unit\":\"{1}\"}}'.format(extra_specs['hw:mem_page_size'],"KB")
                         })
        except Exception:
            self._logger.error(traceback.format_exc())

        return hugepages_capability

    def _get_numa_capabilities(self, extra_specs):
        numa_capability = {}
        feature_uuid = uuid.uuid4()

        try:
            if extra_specs.has_key('hw:numa_nodes'):
                numa_capability['hpa-capability-id'] = str(feature_uuid)
                numa_capability['hpa-feature'] = 'numa'
                numa_capability['architecture'] = 'generic'
                numa_capability['hpa-version'] = 'v1'

                numa_capability['hpa-feature-attributes'] = []
                numa_capability['hpa-feature-attributes'].append(
                    {'hpa-attribute-key': 'numaNodes',
                     'hpa-attribute-value':
                         '{{\"value\":\"{0}\"}}'.format(extra_specs['hw:numa_nodes'] or 0)
                     })

                for num in range(0, int(extra_specs['hw:numa_nodes'])):
                    numa_cpu_node = "hw:numa_cpus.%s" % num
                    numa_mem_node = "hw:numa_mem.%s" % num
                    numacpu_key = "numaCpu-%s" % num
                    numamem_key = "numaMem-%s" % num

                    if extra_specs.has_key(numa_cpu_node) and extra_specs.has_key(numa_mem_node):
                        numa_capability['hpa-feature-attributes'].append(
                            {'hpa-attribute-key': numacpu_key,
                             'hpa-attribute-value':
                                 '{{\"value\":\"{0}\"}}'.format(extra_specs[numa_cpu_node])
                             })
                        numa_capability['hpa-feature-attributes'].append(
                            {'hpa-attribute-key': numamem_key,
                             'hpa-attribute-value':
                                 '{{\"value\":\"{0}\",\"unit\":\"{1}\"}}'.format(extra_specs[numa_mem_node],"MB")
                             })
        except Exception:
            self._logger.error(traceback.format_exc())

        return numa_capability

    def _get_storage_capabilities(self, flavor):
        storage_capability = {}
        feature_uuid = uuid.uuid4()

        try:
            storage_capability['hpa-capability-id'] = str(feature_uuid)
            storage_capability['hpa-feature'] = 'localStorage'
            storage_capability['architecture'] = 'generic'
            storage_capability['hpa-version'] = 'v1'

            storage_capability['hpa-feature-attributes'] = []
            storage_capability['hpa-feature-attributes'].append(
                {'hpa-attribute-key': 'diskSize',
                 'hpa-attribute-value':
                     '{{\"value\":\"{0}\",\"unit\":\"{1}\"}}'.format(
                         flavor['disk'] or 0, "GB")
                 })
            storage_capability['hpa-feature-attributes'].append(
                {'hpa-attribute-key': 'swapMemSize',
                 'hpa-attribute-value':
                     '{{\"value\":\"{0}\",\"unit\":\"{1}\"}}'.format(
                         flavor['swap'] or 0, "MB")
                 })
            storage_capability['hpa-feature-attributes'].append(
                {'hpa-attribute-key': 'ephemeralDiskSize',
                 'hpa-attribute-value':
                     '{{\"value\":\"{0}\",\"unit\":\"{1}\"}}'.format(
                         flavor['OS-FLV-EXT-DATA:ephemeral'] or 0, "GB")
                 })
        except Exception:
            self._logger.error(traceback.format_exc())

        return storage_capability

    def _get_instruction_set_capabilities(self, extra_specs):
        instruction_capability = {}
        feature_uuid = uuid.uuid4()
        try:
            if extra_specs.has_key('hw:capabilities:cpu_info:features'):
                instruction_capability['hpa-capability-id'] = str(feature_uuid)
                instruction_capability['hpa-feature'] = 'instructionSetExtensions'
                instruction_capability['architecture'] = 'Intel64'
                instruction_capability['hpa-version'] = 'v1'

                instruction_capability['hpa-feature-attributes'] = []
                instruction_capability['hpa-feature-attributes'].append(
                    {'hpa-attribute-key': 'instructionSetExtensions',
                     'hpa-attribute-value':
                         '{{\"value\":\"{0}\"}}'.format(
                             extra_specs['hw:capabilities:cpu_info:features'])
                     })
        except Exception:
            self._logger.error(traceback.format_exc())

        return instruction_capability

    def _get_pci_passthrough_capabilities(self, extra_specs):
        pci_passthrough_capability = {}
        feature_uuid = uuid.uuid4()

        try:

            if extra_specs.has_key('pci_passthrough:alias'):
                value1 = extra_specs['pci_passthrough:alias'].split(':')
                value2 = value1[0].split('-')

                pci_passthrough_capability['hpa-capability-id'] = str(feature_uuid)
                pci_passthrough_capability['hpa-feature'] = 'pciePassthrough'
                pci_passthrough_capability['architecture'] = str(value2[2])
                pci_passthrough_capability['hpa-version'] = 'v1'


                pci_passthrough_capability['hpa-feature-attributes'] = []
                pci_passthrough_capability['hpa-feature-attributes'].append(
                    {'hpa-attribute-key': 'pciCount',
                     'hpa-attribute-value':
                         '{{\"value\":\"{0}\"}}'.format(value1[1])
                     })
                pci_passthrough_capability['hpa-feature-attributes'].append(
                    {'hpa-attribute-key': 'pciVendorId',
                     'hpa-attribute-value':
                         '{{\"value\":\"{0}\"}}'.format(value2[3])
                     })
                pci_passthrough_capability['hpa-feature-attributes'].append(
                    {'hpa-attribute-key': 'pciDeviceId',
                     'hpa-attribute-value':
                         '{{\"value\":\"{0}\"}}'.format(value2[4])
                                                                         })
        except Exception:
            self._logger.error(traceback.format_exc())

        return pci_passthrough_capability

    def _get_sriov_nic_capabilities(self, extra_specs):
        sriov_capability = {}
        feature_uuid = uuid.uuid4()

        try:
            if extra_specs.has_key('aggregate_instance_extra_specs:sriov_nic'):
                value1 = extra_specs['aggregate_instance_extra_specs:sriov_nic'].split(':')
                value2 = value1[0].split('-', 5)

                sriov_capability['hpa-capability-id'] = str(feature_uuid)
                sriov_capability['hpa-feature'] = 'sriovNICNetwork'
                sriov_capability['architecture'] = str(value2[2])
                sriov_capability['hpa-version'] = 'v1'

                sriov_capability['hpa-feature-attributes'] = []
                sriov_capability['hpa-feature-attributes'].append(
                    {'hpa-attribute-key': 'pciCount',
                     'hpa-attribute-value':
                         '{{\"value\":\"{0}\"}}'.format(value1[1])})
                sriov_capability['hpa-feature-attributes'].append(
                    {'hpa-attribute-key': 'pciVendorId',
                     'hpa-attribute-value':
                         '{{\"value\":\"{0}\"}}'.format(value2[3])})
                sriov_capability['hpa-feature-attributes'].append(
                    {'hpa-attribute-key': 'pciDeviceId',
                     'hpa-attribute-value':
                         '{{\"value\":\"{0}\"}}'.format(value2[4])})
                sriov_capability['hpa-feature-attributes'].append(
                    {'hpa-attribute-key': 'physicalNetwork',
                     'hpa-attribute-value':
                         '{{\"value\":\"{0}\"}}'.format(value2[5])})
        except Exception:
            self._logger.error(traceback.format_exc())

        return sriov_capability

    def _get_ovsdpdk_capabilities(self, extra_specs, viminfo):
        ovsdpdk_capability = {}
        feature_uuid = uuid.uuid4()

        try:
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
                            'hpa-attribute-value': '{{\"value\":\"{0}\"}}'.format(
                                cloud_dpdk_info.get("libversion"))
                        },]
        except Exception:
            self._logger.error(traceback.format_exc())

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
                    self._logger.debug(
                        "failed to populate image info into AAI: %s,"
                        " image id: %s, ret:%s"
                        % (vimid, image_info['image-id'], ret))
                    continue

                schema = image['schema']
                if schema:
                    req_resource = schema
                    service = {'service_type': "image",
                               'interface': 'public',
                               'region_name': viminfo['openstack_region_id']
                               if viminfo.get('openstack_region_id')
                               else viminfo['cloud_region_id']
                               }

                    self._logger.info("making request with URI:%s" %
                                      req_resource)
                    resp = session.get(req_resource, endpoint_filter=service)
                    self._logger.info("request returns with status %s" %
                                      resp.status_code)
                    if resp.status_code == status.HTTP_200_OK:
                        self._logger.debug("with content:%s" %
                                           resp.json())
                        pass
                    content = resp.json()

                    # if resp.status_code == status.HTTP_200_OK:
                        # parse the schema? TBD
                        # self.update_image(cloud_owner, cloud_region_id, image_info)
                        #metadata_info = {}
            return (0, "succeed")
        except VimDriverNewtonException as e:
            self._logger.error("VimDriverNewtonException:"
                               " status:%s, response:%s" %
                               (e.http_status, e.content))
            return (
                e.http_status, e.content
            )
        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s" %
                               (e.http_status, e.response.json()))
            return (
                e.http_status, e.response.json()
            )
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return (
                11, e.message
            )

    def _discover_availability_zones(self, vimid="", session=None,
                                     viminfo=None):
        try:
            az_pserver_info = {}
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
                # filter out the default az: "internal" and "nova"
                azName = az.get('zoneName', None)
                # comment it for test the registration process only
                #  if azName == 'nova':
                #    continue
                if azName == 'internal':
                    continue

                # get list of host names
                pservers_info = [k for (k, v) in az['hosts'].items()]
                # set the association between az and pservers
                az_pserver_info[azName] = pservers_info

                az_info['hypervisor-type'] = 'QEMU' # default for OpenStack

                ret, content = self._update_resoure(
                    cloud_owner, cloud_region_id, az['zoneName'], az_info,
                    "availability-zone")
                if ret != 0:
                    # failed to update image
                    self._logger.debug(
                        "failed to populate az info into AAI: "
                        "%s, az name: %s, ret:%s"
                        % (vimid, az_info['availability-zone-name'], ret))
                    # return (
                    #     ret,
                    #     "fail to popluate az info into AAI:%s" % content
                    # )
                    continue

                # populate pservers:
                for hostname in pservers_info:
                    if hostname == "":
                        continue

                    pservername = vimid+"_"+hostname
                    selflink = ""
                    # if self.proxy_prefix[3:] == "/v1":
                    #     selflink = "%s/%s/%s/compute/os-hypervisors/detail?hypervisor_hostname_pattern=%s"%\
                    #            (self.proxy_prefix, cloud_owner, cloud_region_id , hostname)
                    # else:
                    #     selflink = "%s/%s/compute/os-hypervisors/detail?hypervisor_hostname_pattern=%s" % \
                    #                (self.proxy_prefix, vimid, hostname)

                    pinfo = {
                        "hostname": pservername,
                        "server-selflink": selflink,
                        "pserver-id": hostname
                    }
                    self._update_pserver(cloud_owner, cloud_region_id, pinfo)
                    self._update_pserver_relation_az(cloud_owner, cloud_region_id, pinfo, azName)
                    self._update_pserver_relation_cloudregion(cloud_owner, cloud_region_id, pinfo)

            return (0, az_pserver_info)
        except VimDriverNewtonException as e:
            self._logger.error(
                "VimDriverNewtonException: status:%s,"
                " response:%s" % (e.http_status, e.content))
            return (
                e.http_status, e.content
            )
        except HttpError as e:
            self._logger.error(
                "HttpError: status:%s, response:%s" %
                (e.http_status, e.response.json()))
            return (
                e.http_status, e.response.json()
            )
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return (
                11, e.message
            )

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

                ret, content = self._update_resoure(
                    cloud_owner, cloud_region_id, ss['id'], snapshot_info,
                    "snapshot")
                if ret != 0:
                    # failed to update image
                    self._logger.debug("failed to populate snapshot info into AAI: %s, snapshot-id: %s, ret:%s"
                                       % (vimid, snapshot_info['snapshot-id'], ret))
                    return (
                        ret,
                        "fail to populate snapshot into AAI:%s" % content
                    )
            return 0, "Succeed"
        except VimDriverNewtonException as e:
            self._logger.error("VimDriverNewtonException: status:%s, response:%s" % (e.http_status, e.content))
            return (
                e.http_status, e.content
            )
        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return (
                e.http_status, e.response.json()
            )
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return (
                11, e.message
            )

    # def _discover_servergroups(self, vimid="", session=None, viminfo=None):
    #     for sg in self._get_list_resources(
    #             "/os-server-groups", "compute", session,
    #             viminfo, vimid,
    #             "security groups"):

    def _update_pserver_relation_az(self, cloud_owner, cloud_region_id, pserverinfo, azName):
        related_link = \
            "/aai/%s/cloud-infrastructure/cloud-regions/"\
            "cloud-region/%s/%s/"\
            "availability-zones/availability-zone/%s" % (
                settings.AAI_SCHEMA_VERSION, cloud_owner,
                cloud_region_id, azName)

        relationship_data = \
            {
                'related-to': 'availability-zone',
                'related-link': related_link,
                'relationship-data': [
                    {
                        'relationship-key': 'availability-zone.availability-zone-name',
                        'relationship-value': azName
                    }
                ],
                "related-to-property": [
                    {
                        "property-key": "availability-zone.availability-zone-name"
                    }
                ]
            }

        retcode, content, status_code = \
            restcall.req_to_aai("/cloud-infrastructure/pservers/pserver/%s"
                                "/relationship-list/relationship"
                                % (pserverinfo['hostname']), "PUT",
                                content=relationship_data)

        self._logger.debug("update_pserver_az_relation,vimid:%s_%s, "
                           "az:%s req_to_aai: %s, return %s, %s, %s"
                           % (cloud_owner, cloud_region_id, azName,
                              pserverinfo['hostname'], retcode, content,
                              status_code))
        return (
            0,
            "succeed"
        )

    def _update_pserver_relation_cloudregion(
            self,
            cloud_owner,
            cloud_region_id,
            pserverinfo
    ):
        related_link = \
            "/aai/%s/cloud-infrastructure/cloud-regions/"\
            "cloud-region/%s/%s" % (
                settings.AAI_SCHEMA_VERSION, cloud_owner,
                cloud_region_id)

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
            restcall.req_to_aai("/cloud-infrastructure/pservers/pserver"
                                "/%s/relationship-list/relationship"
                                % (pserverinfo['hostname']), "PUT",
                                content=relationship_data)

        self._logger.debug("update_pserver_cloudregion_relation,vimid:%s_%s"
                           " req_to_aai: %s, return %s, %s, %s"
                           % (cloud_owner, cloud_region_id,
                              pserverinfo['hostname'], retcode, content,
                              status_code))
        return (
            0,
            "succeed"
        )

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

            self._logger.debug(
                "update_snapshot,vimid:%s_%s req_to_aai: %s,"
                " return %s, %s, %s" % (
                    cloud_owner, cloud_region_id,
                    pserverinfo['hostname'],
                    retcode, content, status_code))

            return retcode, content
        else:
            # unknown cloud owner,region_id
            return (
                10,
                "Cloud Region not found: %s,%s"
                % (cloud_owner, cloud_region_id)
            )

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

                if hypervisor.get('cpu_info'):
                    cpu_info = json.loads(hypervisor['cpu_info'])
                    if cpu_info.get('topology'):
                        cputopo = cpu_info.get('topology')
                        n_cpus = cputopo['cores'] * cputopo['threads'] * cputopo['sockets']
                        hypervisor_info['number-of-cpus'] = n_cpus

                ret, content = self._update_pserver(cloud_owner, cloud_region_id,
                                          hypervisor_info)
                if ret != 0:
                    # failed to update image
                    self._logger.debug(
                        "failed to populate pserver info into AAI:"
                        " %s, hostname: %s, ret:%s"
                        % (vimid, hypervisor_info['hostname'], ret))
                    return ret, "fail to update pserver to AAI:%s" % content

            return 0, "succeed"
        except VimDriverNewtonException as e:
            self._logger.error(
                "VimDriverNewtonException: status:%s, response:%s"
                % (e.http_status, e.content))
            return (
                e.http_status, e.content
            )
        except HttpError as e:
            self._logger.error(
                "HttpError: status:%s, response:%s"
                % (e.http_status, e.response.json()))
            return (
                e.http_status, e.response.json()
            )
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return (
                11, e.message
            )

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
                resource_url = \
                    "/cloud-infrastructure/cloud-regions" \
                    "/cloud-region/%s/%s" \
                    % (cloud_owner, cloud_region_id)

                # get cloud-region
                retcode, content, status_code = \
                    restcall.req_to_aai(resource_url, "GET")

                # add resource-version to url
                if retcode == 0 and content:
                    viminfo = json.JSONDecoder().decode(content)
                    viminfo['identity-url'] =\
                        self.proxy_prefix + "/%s/identity/v2.0" % vimid \
                            if self.proxy_prefix[-3:] == "/v0" \
                            else self.proxy_prefix +\
                                 "/%s/%s/identity/v2.0"\
                                 % extsys.decode_vim_id(vimid)

                    retcode, content, status_code = \
                        restcall.req_to_aai(
                            "/cloud-infrastructure/cloud-regions"
                            "/cloud-region/%s/%s"
                            % (cloud_owner, cloud_region_id), "PUT",
                            content=viminfo)

                    self._logger.debug(
                        "update_proxy_identity_endpoint,vimid:"
                        "%s req_to_aai: %s, return %s, %s, %s"
                        % (vimid, viminfo['identity-url'],
                           retcode, content, status_code))
                    return 0, "succeed"
                else:
                    self._logger.debug(
                        "failure: update_proxy_identity_endpoint,vimid:"
                        "%s req_to_aai: return %s, %s, %s"
                        % (vimid, retcode, content, status_code))
                    return retcode, content
            else:
                return (
                    10,
                    "Cloud Region not found: %s" % vimid
                )

        except VimDriverNewtonException as e:
            self._logger.error(
                "VimDriverNewtonException: status:%s, response:%s"
                % (e.http_status, e.content))
            return (
                e.http_status, e.content
            )
        except HttpError as e:
            self._logger.error(
                "HttpError: status:%s, response:%s"
                % (e.http_status, e.response.json()))
            return (
                e.http_status, e.response.json()
            )
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return (
                11, e.message
            )

