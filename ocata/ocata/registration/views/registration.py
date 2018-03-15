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

logger = logging.getLogger(__name__)

DEBUG=True

class Registry(newton_registration.Registry):

    def __init__(self):
        self.proxy_prefix = settings.MULTICLOUD_PREFIX
        self.aai_base_url = settings.AAI_BASE_URL
        self._logger = logger

    def _discover_flavors(self, vimid="", session=None, viminfo=None):
        try:
            cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)
            hpa_caps = []
            hpa_caps.append("[")
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
                
                # add hpa capabilities
                if (flavor['name'].find('onap.') == -1):
                    continue
                
                properties = flavor['properties'].split(', ')
                if len(properties):
                    flavor_info['flavor-properties'] = flavor['properties']
                    # add hpa capability cpu pinning
                    if (flavor['name'].find('onap.cpu_pinning') != -1):
                        uuid1 = uuid.uuid4()
                        hpa_caps.append("{'hpaCapabilityID': '" + str(uuid1) + "', ")
                        hpa_caps.append("'hpaFeature': 'cpuPinning', ")
                        hpa_caps.append("'hardwareArchitecture': 'generic', ")
                        hpa_caps.append("'version': 'v1', ")

                        hpa_caps.append("[")
                        for p in range(len(properties)):
                            if (properties[p] == "hw:cpu_policy") :
                                hpa_caps.append("{'hpa-attribute-key':'logicalCpuThreadPinningPolicy', ")
                                hpa_caps.append("'hpa-attribute-value': {'value':'prefer'}}, ")
                            if (properties[p] == "hw:cpu_thread_policy") :
                                hpa_caps.append("{'hpa-attribute-key':'logicalCpuPinningPolicy', ")
                                hpa_caps.append("'hpa-attribute-value': {'value':'dedicated'}}, ")
                        hpa_caps.append("]},")
                    else:
                        self._logger.info("can not support this properties")
                else:
                    self._logger.info("can not support this flavor type")
                hpa_caps.append("]")
                str_hpa_caps = ''
                flavor_info['hpa_capabilities'] = str_hpa_caps.join(hpa_caps)
                self._logger.debug("flavor_info: %s" % flavor_info)
  
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
