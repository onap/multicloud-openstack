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
from common.exceptions import VimDriverNewtonException
from common.msapi import extsys
from keystoneauth1.exceptions import HttpError
from newton_base.util import VimDriverUtils
from common.utils import restcall

logger = logging.getLogger(__name__)

# DEBUG=True

class Registry(newton_registration.Registry):

    def __init__(self):
        super(Registry, self).__init__()
        self.proxy_prefix = settings.MULTICLOUD_PREFIX
        self.aai_base_url = settings.AAI_BASE_URL
        # self._logger = logger

class APIv1Registry(Registry):

    def __init__(self):
        super(APIv1Registry, self).__init__()
        self.proxy_prefix = settings.MULTICLOUD_API_V1_PREFIX
        self.aai_base_url = settings.AAI_BASE_URL
        # self._logger = logger


    def _update_cloud_region(self, cloud_owner, cloud_region_id, openstack_region_id, viminfo, session=None):
        if cloud_owner and cloud_region_id:
            self._logger.debug(
                ("_update_cloud_region, %(cloud_owner)s"
                 "_%(cloud_region_id)s ")
                % {
                    "cloud_owner": cloud_owner,
                    "cloud_region_id": cloud_region_id
                })

            #Note1: The intent is to populate the openstack region id into property: cloud-region.esr-system-info.openstackRegionId
            #Note2: As temp solution: the openstack region id was put into AAI cloud-region["cloud-epa-caps"]

            resource_info = {
                "cloud-owner": cloud_owner,
                "cloud-region-id": cloud_region_id,
                "cloud-type": viminfo["type"],
                "cloud-region-version": viminfo["version"],
                "identity-url": self.proxy_prefix + "/%s/%s/identity/v2.0" % (cloud_owner, cloud_region_id),
                "complex-name": viminfo["complex-name"],
                "cloud-extra-info": viminfo["cloud_extra_info"],
                "cloud-epa-caps":openstack_region_id,
                "esr-system-info-list":{
                    "esr-system-info":[
                        {
                            "esr-system-info-id": str(uuid.uuid4()),
                            "service-url": viminfo["url"],
                            "user-name": viminfo["userName"],
                            "password": viminfo["password"],
                            "system-type":"VIM",
                            "ssl-cacert":viminfo["cacert"],
                            "ssl-insecure": viminfo["insecure"],
                            "cloud-domain": viminfo["domain"],
                            "default-tenant": viminfo["tenant"]

                        }
                    ]
                }
            }

            #get the resource first
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
                #resource_info["resource-version"] = content["resource-version"]
                content.update(resource_info)
                resource_info = content

            #then update the resource
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
            return retcode
        return 1  # unknown cloud owner,region_id

    def _discover_regions(self, cloud_owner="", cloud_region_id="", session=None, viminfo=None):
        try:
            regions = []
            vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
            for region in self._get_list_resources(
                    "/regions", "identity", session, viminfo, vimid,
                    "regions"):
                if (region['id'] == 'SystemController'):
                    continue
                elif (region['id'] == 'RegionOne'):
                    continue
                else:
                    regions.append(region['id'])


            return regions

        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return

    def post(self, request, cloud_owner="", cloud_region_id=""):
        self._logger.info("registration with : %s, %s" % (cloud_owner, cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)

        viminfo = VimDriverUtils.get_vim_info(vimid)
        cloud_extra_info = viminfo['cloud_extra_info']
        region_specified = cloud_extra_info["openstack-region-id"] if cloud_extra_info else None
        multi_region_discovery = cloud_extra_info["multi-region-discovery"] if cloud_extra_info else None

        # discover the regions
        region_ids = self._discover_regions(cloud_owner, cloud_region_id, None, viminfo)

        # compare the regions with region_specified and then cloud_region_id
        if (region_specified in region_ids):
            pass
        elif (cloud_region_id in region_ids):
            region_specified = cloud_region_id
            pass
        else:
            # assume the first region be the primary region since we have no other way to determine it.
            region_specified = region_ids[0]

        # update cloud region and discover/register resource
        if (multi_region_discovery and multi_region_discovery.upper() == "TRUE"):
            # no input for specified cloud region, so discover all cloud region?
            for regionid in region_ids:
                #create cloud region with composed AAI cloud_region_id except for the one onboarded externally (e.g. ESR)
                gen_cloud_region_id = cloud_region_id + "." + regionid if region_specified != regionid else cloud_region_id
                self._update_cloud_region(cloud_owner, gen_cloud_region_id, regionid, viminfo)
                return super(RegistryV1, self).post(request, vimid)
        else:
            self._update_cloud_region(cloud_owner, cloud_region_id, region_specified, viminfo)
            return super(RegistryV1, self).post(request, vimid)




    def delete(self, request, cloud_owner="", cloud_region_id=""):
        self._logger.debug("unregister cloud region: %s, %s" % (cloud_owner, cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1Registry, self).delete(request, vimid)
