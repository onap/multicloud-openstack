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

from django.conf import settings

from newton_base.registration import registration as newton_registration
from rest_framework import status
from rest_framework.response import Response
from common.msapi import extsys
from common.msapi import helper
from keystoneauth1.exceptions import HttpError
from newton_base.util import VimDriverUtils
from common.utils import restcall
from django.core.cache import cache

logger = logging.getLogger(__name__)

# global var: Audition thread
gAZCapAuditThread = helper.MultiCloudThreadHelper("azcap")

# DEBUG=True

# APIv0 handler upgrading: leverage APIv1 handler
class APIv0Registry(newton_registration.Registry):
    def __init__(self):
        # logger.error(traceback.format_exc())
        self.register_helper = RegistryHelper(settings.MULTICLOUD_PREFIX, settings.AAI_BASE_URL)
        super(APIv0Registry, self).__init__()
        # self._logger = logger

    def post(self, request, vimid=""):
        self._logger.info("registration with :  %s" % vimid)

        # Get the specified tenant id
        specified_project_idorname = request.META.get("Project", None)

        # vim registration will trigger the start the audit of AZ capacity
        worker_self = InfraResourceAuditor(
            settings.MULTICLOUD_API_V1_PREFIX,
            settings.AAI_BASE_URL
        )
        backlog_item = {
            "id": vimid,
            "worker": worker_self.azcap_audit,
            "payload": (vimid, specified_project_idorname),
            "repeat": 10*1000000,  # repeat every 10 seconds
        }
        gAZCapAuditThread.add(backlog_item)
        if 0 == gAZCapAuditThread.state():
            gAZCapAuditThread.start()
        return super(APIv0Registry, self).post(request, vimid)

    def delete(self, request, vimid=""):
        self._logger.debug("unregister cloud region: %s" % vimid)
        gAZCapAuditThread.remove(vimid)
        return super(APIv0Registry, self).delete(request, vimid)


class Registry(APIv0Registry):
    def __init__(self):
        super(Registry, self).__init__()


class APIv1Registry(newton_registration.Registry):
    def __init__(self):
        self.register_helper = RegistryHelper(settings.MULTICLOUD_API_V1_PREFIX, settings.AAI_BASE_URL)
        super(APIv1Registry, self).__init__()
        # self._logger = logger

    def post(self, request, cloud_owner="", cloud_region_id=""):
        self._logger.info("registration with : %s, %s"
                          % (cloud_owner, cloud_region_id))

        try:
            # Get the specified tenant id
            specified_project_idorname = request.META.get("Project", None)

            vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)

            # vim registration will trigger the start the audit of AZ capacity
            worker_self = InfraResourceAuditor(
                settings.MULTICLOUD_API_V1_PREFIX,
                settings.AAI_BASE_URL
            )
            backlog_item = {
                "id": vimid,
                "worker": worker_self.azcap_audit,
                "payload": (vimid, specified_project_idorname),
                "repeat": 5 * 1000000,  # repeat every 5 seconds
            }
            gAZCapAuditThread.add(backlog_item)
            if 0 == gAZCapAuditThread.state():
                gAZCapAuditThread.start()

            return super(APIv1Registry, self).post(request, vimid)

        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s"
                               % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return Response(
                data={'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, cloud_owner="", cloud_region_id=""):
        self._logger.debug("unregister cloud region: %s, %s"
                           % (cloud_owner, cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        gAZCapAuditThread.remove(vimid)
        return super(APIv1Registry, self).delete(request, vimid)


class RegistryHelper(newton_registration.RegistryHelper):
    '''
    Helper code to discover and register a cloud region's resource
    '''
    def __init__(self, multicloud_prefix, aai_base_url):
        # logger.error(traceback.format_exc())
        super(RegistryHelper, self).__init__(multicloud_prefix, aai_base_url)
        # self._logger = logger

    def registryV0(self, vimid="", project_idorname=None):
        '''
        extend base method
        '''
        viminfo = VimDriverUtils.get_vim_info(vimid)

        if not viminfo:
            return (
                10,
                "Cloud Region not found in AAI: %s" % vimid
            )

        cloud_extra_info_str = viminfo['cloud_extra_info']
        cloud_extra_info = None
        try:
            cloud_extra_info = json.loads(cloud_extra_info_str) \
                if cloud_extra_info_str else None
        except Exception as ex:
            logger.error("Can not convert cloud extra info %s %s" % (
                str(ex), cloud_extra_info_str))
            pass

        region_specified = cloud_extra_info.get(
            "openstack-region-id", None) if cloud_extra_info else None
        multi_region_discovery = cloud_extra_info.get(
            "multi-region-discovery", None) if cloud_extra_info else None

        sess = None
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

        # discover the regions, expect it always returns a list (even empty list)
        cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)
        # region_ids = self._discover_regions(cloud_owner, cloud_region_id, sess, viminfo)
        region_ids = self._discover_regions(vimid, sess, viminfo)

        if len(region_ids) == 0:
            self._logger.warn("failed to get region id")

        # compare the regions with region_specified and then cloud_region_id
        if region_specified in region_ids:
            pass
        elif cloud_region_id in region_ids:
            region_specified = cloud_region_id
            pass
        else:
            # assume the first region be the primary region
            # since we have no other way to determine it.
            region_specified = region_ids.pop(0)

        # update cloud region and discover/register resource
        if multi_region_discovery:
            # no input for specified cloud region,
            # so discover all cloud region
            for regionid in region_ids:
                # do not update the specified region here
                if region_specified == regionid:
                    continue

                # create cloud region with composed AAI cloud_region_id
                # except for the one onboarded externally (e.g. ESR)
                gen_cloud_region_id = cloud_region_id + "_" + regionid
                self._logger.info("create a cloud region: %s,%s,%s"
                                  % (cloud_owner, gen_cloud_region_id, regionid))

                try:
                    self._update_cloud_region(
                        cloud_owner, gen_cloud_region_id, regionid, viminfo)
                except Exception as e:
                    self._logger.debug("update cloud region fails %s" % e.message)

                try:
                    new_vimid = extsys.encode_vim_id(
                        cloud_owner, gen_cloud_region_id)
                    super(RegistryHelper, self).registryV0(new_vimid, project_idorname)
                except Exception as e:
                    self._logger.debug("registryV0 fails %s" % e.message)

        # update the specified region
        try:
            self._update_cloud_region(cloud_owner, cloud_region_id,
                                      region_specified, viminfo)
        except Exception as e:
            self._logger.debug("update cloud region fails %s" % e.message)

        try:
            super(RegistryHelper, self).registryV0(vimid, project_idorname)
        except Exception as e:
            self._logger.debug("registryV0 fails %s" % e.message)

        return 0

    def unregistry(self, vimid=""):
        '''extend base method'''

        return self.super(RegistryHelper, self).unregistry(vimid)

    def _get_ovsdpdk_capabilities(self, extra_specs, viminfo):
        '''extend base method'''

        instruction_capability = {}
        feature_uuid = uuid.uuid4()

        instruction_capability['hpa-capability-id'] = str(feature_uuid)
        instruction_capability['hpa-feature'] = 'ovsDpdk'
        instruction_capability['architecture'] = 'Intel64'
        instruction_capability['hpa-version'] = 'v1'

        instruction_capability['hpa-feature-attributes'] = []
        instruction_capability['hpa-feature-attributes'].append(
            {'hpa-attribute-key': 'dataProcessingAccelerationLibrary',
             'hpa-attribute-value':
                 '{{\"value\":\"{0}\"}}'.format("v17.02")
             })
        return instruction_capability

    def _update_cloud_region(self, cloud_owner, cloud_region_id, openstack_region_id, viminfo, session=None):
        if cloud_owner and cloud_region_id:
            self._logger.debug(
                ("_update_cloud_region, %(cloud_owner)s"
                 "_%(cloud_region_id)s ")
                % {
                    "cloud_owner": cloud_owner,
                    "cloud_region_id": cloud_region_id
                })

            # Note1: The intent is to populate the openstack region id into property: cloud-region.esr-system-info.openstackRegionId
            # Note2: As temp solution: the openstack region id was put into AAI cloud-region["cloud-epa-caps"]

            resource_info = {
                "cloud-owner": cloud_owner,
                "cloud-region-id": cloud_region_id,
                "cloud-type": viminfo["type"],
                "cloud-region-version": viminfo["version"],
                "identity-url":
                    self.proxy_prefix + "/%s_%s/identity/v2.0" % (cloud_owner, cloud_region_id)
                    if self.proxy_prefix[-3:] == "/v0" else
                    self.proxy_prefix + "/%s/%s/identity/v2.0" % (cloud_owner, cloud_region_id),
                "complex-name": viminfo["complex-name"],
                "cloud-extra-info": viminfo["cloud_extra_info"],
                "cloud-epa-caps": openstack_region_id,
                "esr-system-info-list": {
                    "esr-system-info": [
                        {
                            "esr-system-info-id": str(uuid.uuid4()),
                            "service-url": viminfo["url"],
                            "user-name": viminfo["userName"],
                            "password": viminfo["password"],
                            "system-type": "VIM",
                            "ssl-cacert": viminfo["cacert"],
                            "ssl-insecure": viminfo["insecure"],
                            "cloud-domain": viminfo["domain"],
                            "default-tenant": viminfo["tenant"]

                        }
                    ]
                }
            }

            # get the resource first
            resource_url = ("/cloud-infrastructure/cloud-regions/"
                            "cloud-region/%(cloud_owner)s/%(cloud_region_id)s"
                            % {
                                "cloud_owner": cloud_owner,
                                "cloud_region_id": cloud_region_id
                            })

            # get cloud-region
            retcode, content, status_code = \
                restcall.req_to_aai(resource_url, "GET")

            # add resource-version
            if retcode == 0 and content:
                content = json.JSONDecoder().decode(content)
                # resource_info["resource-version"] = content["resource-version"]
                content.update(resource_info)
                resource_info = content

            # then update the resource
            retcode, content, status_code = \
                restcall.req_to_aai(resource_url, "PUT", content=resource_info)

            self._logger.debug(
                ("_update_cloud_region,%(cloud_owner)s"
                 "_%(cloud_region_id)s , "
                 "return %(retcode)s, %(content)s, %(status_code)s")
                % {
                    "cloud_owner": cloud_owner,
                    "cloud_region_id": cloud_region_id,
                    "retcode": retcode,
                    "content": content,
                    "status_code": status_code,
                })

            # wait and confirm the update has been available for next AAI calls
            while True:
                # get cloud-region
                retcode2, content2, status_code2 = \
                    restcall.req_to_aai(resource_url, "GET")
                if retcode2 == 0 and content2:
                    content2 = json.JSONDecoder().decode(content2)
                    if content2.get("identity-url", None)\
                            == resource_info.get("identity-url", None):
                        break

            return retcode
        return 1  # unknown cloud owner,region_id

    # def _discover_regions(self, cloud_owner="", cloud_region_id="",
    def _discover_regions(self, vimid, session=None, viminfo=None):
        try:
            regions = []
            # vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
            isDistributedCloud = False
            openstackregions = self._get_list_resources(
                "/regions", "identity", session, viminfo, vimid,
                "regions")

            for region in openstackregions:
                if region['id'] == 'SystemController':
                    isDistributedCloud = True
                    break
                else:
                    continue

            for region in openstackregions:
                if region['id'] == 'SystemController':
                    continue
                elif region['id'] == 'RegionOne' and isDistributedCloud:
                    continue
                else:
                    regions.append(region['id'])

            self._logger.info("Discovered Regions :%s" % regions)
            return regions

        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s"
                               % (e.http_status, e.response.json()))
            return []
        except Exception:
            self._logger.error(traceback.format_exc())
            return []


class InfraResourceAuditor(newton_registration.RegistryHelper):

    def __init__(self, multicloud_prefix, aai_base_url):
        self.proxy_prefix = multicloud_prefix
        self.aai_base_url = aai_base_url
        self._logger = logger
        # super(InfraResourceAuditor, self).__init__();

    def azcap_audit(self, vimid, project_idorname=None):
        viminfo = VimDriverUtils.get_vim_info(vimid)
        if not viminfo:
            self._logger.warn("azcap_audit no valid vimid: %s" % vimid)
            return

        sess = None
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
            session = VimDriverUtils.get_session(
                viminfo,
                tenant_name=viminfo['tenant']
            )

        # now retrieve the latest AZ cap info
        try:
            # get all hypervisor detail ?
            hypervisors = self._get_list_resources(
                "/os-hypervisors/detail", "compute", session,
                viminfo, vimid, "hypervisors")

            hypervisors_dict = {}
            # for h in hypervisors:
            #     if not h.get("service", None):
            #         continue
            #     if not h.get("host", None):
            #         continue
            #     hypervisors_dict[h["service"]["host"]] = h
            for h in hypervisors:
                if not h.get("hypervisor_hostname", None):
                    continue
                hypervisors_dict[h["hypervisor_hostname"]] = h

            vimAzCacheKey = "cap_azlist_" + vimid
            vimAzList = []
            # cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)
            for az in self._get_list_resources(
                    "/os-availability-zone/detail", "compute", session,
                    viminfo, vimid,
                    "availabilityZoneInfo"):
                az_info = {
                    'availability-zone-name': az.get('zoneName', ""),
                    'operational-status': az.get('zoneState', {}).get('available', ""),
                    'hypervisor-type': '',
                }
                # filter out the default az: "internal" and "nova"
                azName = az.get('zoneName', None)
                # comment it for test the registration process only
                #  if azName == 'nova':
                #    continue
                if azName == 'internal':
                    continue

                vimAzList.append(azName)

                # get list of host names
                pservers_info = [k for (k, v) in az['hosts'].items()]

                # Get current cap info of azName
                azCapCacheKey = "cap_" + vimid + "_" + azName
                azCapInfoCacheStr = cache.get(azCapCacheKey)
                azCapInfoCache = json.loads(azCapInfoCacheStr) if azCapInfoCacheStr else {}

                for psname in pservers_info:
                    psinfo = hypervisors_dict.get(psname, None)
                    if not psinfo:
                        # warning: the pserver info not found
                        continue
                    # get current pserver cap info
                    psCapInfoCacheKey = "cap_" + vimid + "_" + psname
                    psCapInfoCacheStr = cache.get(psCapInfoCacheKey)
                    psCapInfoCache = json.loads(psCapInfoCacheStr) if psCapInfoCacheStr else {}

                    # compare latest info with cached one
                    vcpu_delta = 0
                    vcpu_used_delta = 0
                    mem_delta = 0
                    mem_free_delta = 0
                    localstorage_delta = 0
                    localstorage_free_delta = 0
                    if psinfo.get("vcpus", 0) != psCapInfoCache.get("vcpus", 0):
                        vcpu_delta += psinfo.get("vcpus", 0) \
                                      - psCapInfoCache.get("vcpus", 0)
                        psCapInfoCache["vcpus"] = psinfo.get("vcpus", 0)
                    if psinfo.get("memory_mb", 0) != psCapInfoCache.get("memory_mb", 0):
                        mem_delta += psinfo.get("memory_mb", 0) \
                                     - psCapInfoCache.get("memory_mb", 0)
                        psCapInfoCache["memory_mb"] = psinfo.get("memory_mb", 0)
                    if psinfo.get("local_gb", 0) != psCapInfoCache.get("local_gb", 0):
                        localstorage_delta += psinfo.get("local_gb", 0) \
                                              - psCapInfoCache.get("local_gb", 0)
                        psCapInfoCache["local_gb"] = psinfo.get("local_gb", 0)
                    if psinfo.get("vcpus_used", 0) != psCapInfoCache.get("vcpus_used", 0):
                        vcpu_used_delta += psinfo.get("vcpus_used", 0)\
                                     - psCapInfoCache.get("vcpus_used", 0)
                        psCapInfoCache["vcpus_used"] = psinfo.get("vcpus_used", 0)
                    if psinfo.get("free_ram_mb", 0) != psCapInfoCache.get("free_ram_mb", 0):
                        mem_free_delta += psinfo.get("free_ram_mb", 0)\
                                     - psCapInfoCache.get("free_ram_mb", 0)
                        psCapInfoCache["free_ram_mb"] = psinfo.get("free_ram_mb", 0)
                    if psinfo.get("free_disk_gb", 0) != psCapInfoCache.get("free_disk_gb", 0):
                        localstorage_free_delta += psinfo.get("free_disk_gb", 0)\
                                     - psCapInfoCache.get("free_disk_gb", 0)
                        psCapInfoCache["free_disk_gb"] = psinfo.get("free_disk_gb", 0)

                    cache.set(psCapInfoCacheKey, json.dumps(psCapInfoCache), 3600 * 24)

                    # now apply the delta to azCapInfo
                    azCapInfoCache["vcpus"] = azCapInfoCache.get("vcpus", 0) + vcpu_delta
                    azCapInfoCache["memory_mb"] = azCapInfoCache.get("memory_mb", 0) + mem_delta
                    azCapInfoCache["local_gb"] = azCapInfoCache.get("local_gb", 0) + localstorage_delta
                    azCapInfoCache["vcpus_used"] = azCapInfoCache.get("vcpus_used", 0) + vcpu_used_delta
                    azCapInfoCache["free_ram_mb"] = azCapInfoCache.get("free_ram_mb", 0) + mem_free_delta
                    azCapInfoCache["free_disk_gb"] = azCapInfoCache.get("free_disk_gb", 0) + localstorage_free_delta
                    pass

                # update the cache
                cache.set(azCapCacheKey, json.dumps(azCapInfoCache), 3600 * 24)
                cache.set(vimAzCacheKey, json.dumps(vimAzList), 3600 * 24)
        except Exception as e:
            self._logger.error("azcap_audit raise exception: %s" % e)
            pass
