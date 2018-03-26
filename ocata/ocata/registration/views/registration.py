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
            cloud_extra_info_str = viminfo.get('cloud_extra_info')
            if cloud_extra_info_str:
                cloud_extra_info = json.loads(cloud_extra_info_str)
                cloud_dpdk_info = cloud_extra_info.get("ovsDpdk")

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

                if (flavor['extra_specs'] == ""):
                    continue

                flavor_info['extra_specs'] = flavor['extra_specs']
                extra_specs = flavor['extra_specs']
                extra_arr = extra_specs.split(', ')
                uuid4 = uuid.uuid4()

                # add ovs dpdk
                hpa_caps.append("{'hpaCapabilityID': '" + str(uuid4) + "', ")
                hpa_caps.append("'hpaFeature': 'ovsDpdk', ")
                hpa_caps.append("'hardwareArchitecture': '" + cloud_dpdk_info.get("arch") + "', ")
                hpa_caps.append("'version': '" + cloud_dpdk_info.get("version") + "', ")
                hpa_caps.append("[")
                hpa_caps.append("{'hpa-attribute-key':'"+ cloud_dpdk_info.get("libname") + "', ")
                hpa_caps.append("'hpa-attribute-value': {'value':'" + cloud_dpdk_info.get("libvalue") + "'}}, ")
                hpa_caps.append("]")
                hpa_caps.append("},")

                # add basic Capabilities
                hpa_caps.append("{'hpaCapabilityID': '" + str(uuid4) + "', ")
                hpa_caps.append("'hpaFeature': 'baseCapabilities', ")
                hpa_caps.append("'hardwareArchitecture': 'generic', ")
                hpa_caps.append("'version': 'v1', ")
                hpa_caps.append("[")
                hpa_caps.append("{'hpa-attribute-key':'numVirtualCpu', ")
                hpa_caps.append("'hpa-attribute-value': {'value':'" + str(flavor_info['vcpus']) + "'}}, ")
                hpa_caps.append("{'hpa-attribute-key':'virtualMemSize', ")
                hpa_caps.append("'hpa-attribute-value': {'value':" + str(flavor_info['mem']) + ", unit:'MB'}}, ")
                hpa_caps.append("]")
                hpa_caps.append("},")

                # add local storage
                hpa_caps.append("{'hpaCapabilityID': '" + str(uuid4) + "', ")
                hpa_caps.append("'hpaFeature': 'localStorage', ")
                hpa_caps.append("'hardwareArchitecture': 'generic', ")
                hpa_caps.append("'version': 'v1', ")
                hpa_caps.append("[")
                hpa_caps.append("{'hpa-attribute-key':'diskSize', ")
                hpa_caps.append("'hpa-attribute-value': {'value':" + str(flavor_info['disk']) + ", unit:'MB'}}, ")
                hpa_caps.append("{'hpa-attribute-key':'ephemeralDiskSize', ")
                hpa_caps.append("'hpa-attribute-value': {'value':" + str(flavor_info['OS-FLV-EXT-DATA:ephemeral']) + ", unit:'MB'}}, ")
                hpa_caps.append("{'hpa-attribute-key':'swapMemSize', ")
                hpa_caps.append("'hpa-attribute-value': {'value':" + str(flavor_info['swap']) + ", unit:'MB'}}, ")
                hpa_caps.append("]")
                hpa_caps.append("},")

                # add hpa capability cpu pinning
                if (extra_specs.find('hw:cpu_policy') != -1):
                    hpa_caps.append("{'hpaCapabilityID': '" + str(uuid4) + "', ")
                    hpa_caps.append("'hpaFeature': 'cpuPinning', ")
                    hpa_caps.append("'hardwareArchitecture': 'generic', ")
                    hpa_caps.append("'version': 'v1', ")
                    hpa_caps.append("[")
                    for p in range(len(extra_arr)):
                        if (extra_arr[p].find("hw:cpu_policy") != -1) :
                            value = extra_arr[p].split('=')[1]
                            hpa_caps.append("{'hpa-attribute-key':'logicalCpuThreadPinningPolicy', ")
                            hpa_caps.append("'hpa-attribute-value': {'value':'" + value + "'}}, ")
                        if (extra_arr[p].find("hw:cpu_thread_policy") != -1) :
                            value = extra_arr[p].split('=')[1]
                            hpa_caps.append("{'hpa-attribute-key':'logicalCpuPinningPolicy', ")
                            hpa_caps.append("'hpa-attribute-value': {'value':'" + value + "'}}, ")
                    hpa_caps.append("]")
                    hpa_caps.append("},")

                # add cpu topology
                if (extra_specs.find('hw:cpu_sockets') != -1):
                    hpa_caps.append("{'hpaCapabilityID': '" + str(uuid4) + "', ")
                    hpa_caps.append("'hpaFeature': 'cpuTopology', ")
                    hpa_caps.append("'hardwareArchitecture': 'generic', ")
                    hpa_caps.append("'version': 'v1', ")
                    hpa_caps.append("[")
                    for p in range(len(extra_arr)):
                        if (extra_arr[p].find("hw:cpu_sockets") != -1) :
                            value = extra_specs[p].split('=')[1]
                            hpa_caps.append("{'hpa-attribute-key':'numCpuSockets', ")
                            hpa_caps.append("'hpa-attribute-value': {'value':'" + value + "'}}, ")
                        if (extra_arr[p].find("hw:cpu_cores") != -1) :
                            value = extra_specs[p].split('=')[1]
                            hpa_caps.append("{'hpa-attribute-key':'numCpuCores', ")
                            hpa_caps.append("'hpa-attribute-value': {'value':'" + value + "'}}, ")
                        if (extra_arr[p].find("hw:cpu_threads") != -1) :
                            value = extra_specs[p].split('=')[1]
                            hpa_caps.append("{'hpa-attribute-key':'numCpuThreads', ")
                            hpa_caps.append("'hpa-attribute-value': {'value':'" + value + "'}}, ")
                    hpa_caps.append("]")
                    hpa_caps.append("},")

                # add numa
                if (extra_specs.find('hw:numa_nodes') != -1):
                    hpa_caps.append("{'hpaCapabilityID': '" + str(uuid4) + "', ")
                    hpa_caps.append("'hpaFeature': 'numa', ")
                    hpa_caps.append("'hardwareArchitecture': 'generic', ")
                    hpa_caps.append("'version': 'v1', ")
                    hpa_caps.append("[")
                    for p in range(len(extra_arr)):
                        if (extra_arr[p].find("hw:numa_nodes") != -1) :
                            p_arr = extra_arr[p].split('=')
                            value = p_arr[1]
                            hpa_caps.append("{'hpa-attribute-key':'numNodes', ")
                            hpa_caps.append("'hpa-attribute-value': {'value':'" + value + "'}}, ")
                        if (extra_arr[p].find("hw:numa_cpus") != -1) :
                            p_arr = extra_arr[p].split('=')
                            value = p_arr[1]
                            index = p_arr[0].split('.')[1]
                            hpa_caps.append("{'hpa-attribute-key':'numaCpus-" + index + "', ")
                            hpa_caps.append("'hpa-attribute-value': {'value':'[" + value + "]'}}, ")
                        if (extra_arr[p] == ("hw:numa_mem") != -1) :
                            p_arr = extra_arr[p].split('=')
                            value = p_arr[1]
                            index = p_arr[0].split('.')[1]
                            hpa_caps.append("{'hpa-attribute-key':'numaMem-"+ index +"', ")
                            hpa_caps.append("'hpa-attribute-value': {'value':'" + value + ", unit:'MB'}}, ")
                    hpa_caps.append("]")
                    hpa_caps.append("},")

                # add huge page
                if (extra_specs.find('hw:mem_page_size') != -1):
                    hpa_caps.append("{'hpaCapabilityId': '" + str(uuid4) + "', ")
                    hpa_caps.append("'hpaFeature': 'hugePages', ")
                    hpa_caps.append("'hardwareArchitecture': 'generic', ")
                    hpa_caps.append("'version': 'v1', ")
                    hpa_caps.append("[")
                    for p in range(len(extra_arr)):
                        if (extra_arr[p] == "hw:mem_page_size") :
                            value = extra_specs[p].split('=')[1]
                            hpa_caps.append("{'hpa-attribute-key':'memoryPageSize', ")
                            hpa_caps.append("'hpa-attribute-value': {'value':'" + value + "'}}, ")
                    hpa_caps.append("]")
                    hpa_caps.append("},")

                # add instruction set externsions
                if (extra_specs.find('w:capabilities:cpu_info:features') != -1):
                    hpa_caps.append("{'hpaCapabilityId': '" + str(uuid4) + "', ")
                    hpa_caps.append("'hpaFeature': 'instructionSetExtensions', ")
                    hpa_caps.append("'hardwareArchitecture': 'Intel64', ")
                    hpa_caps.append("'version': 'v1', ")
                    hpa_caps.append("[")
                    for p in range(len(extra_arr)):
                        if (extra_arr[p].find("hw:capabilities:cpu_info:features") != -1) :
                            value = extra_arr.split('=')[1]
                            hpa_caps.append("{'hpa-attribute-key':'instructionSetExtensions', ")
                            hpa_caps.append("'hpa-attribute-value': {'value':[" + value + "]}}, ")
                    hpa_caps.append("]")
                    hpa_caps.append("},")

                # add pci device passthrough
                if (extra_specs.find('pci_passthrough:alias') != -1) :
                    hpa_caps.append("{'hpaCapabilityId': '" + str(uuid4) + "', ")
                    hpa_caps.append("'hpaFeature': 'pciPassthrough', ")
                    hpa_caps.append("'version': 'v1', ")
                    hpa_caps.append("[")
                    for p in range(len(extra_arr)):
                        if (extra_arr[p] == "pci_passthrough:alias") :
                            values = extra_arr[0].split('-')
                            value = values[4].split(':')
                            hpa_caps.append("{'hpa-attribute-key':'pciCount', ")
                            hpa_caps.append("'hpa-attribute-value': {'value':'" + value[1] + "'}}, ")
                            hpa_caps.append("{'hpa-attribute-key':'pciVendorId', ")
                            hpa_caps.append("'hpa-attribute-value': {'value':'" + values[3] + "'}}, ")
                            hpa_caps.append("{'hpa-attribute-key':'pciDeviceId', ")
                            hpa_caps.append("'hpa-attribute-value': {'value':'" + value[0] + "'}}, ")
                            hpa_caps.append("]")
                    hpa_caps.append("},")
                    hpa_caps.append("]")
                    hpa_caps.append("'hardwareArchitecture': '" + values[2] + "', ")

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

    def _update_epa_caps(self, cloud_owner, cloud_region_id, cloud_extra_info):
        '''
        populate cloud EPA Capabilities information into AAI
        :param cloud_owner:
        :param cloud_region_id:
        :param epa_caps_info: dict of meta data about cloud-region's epa caps

        :return:
        '''
        cloud_epa_caps_info = {}
        cloud_epa_caps_info.update(cloud_extra_info.get("epa-caps"))
        cloud_hpa_info = cloud_extra_info.get("ovsDpdk")
        cloud_epa_caps = {
            'cloud-epa-caps': json.dumps(epa_caps_info),
        }

        if cloud_hpa_info:
            attributes = [
                {
                    'hpa-attribute-key': cloud_hpa_info.get("libname"),
                    'hpa-attribute-value': cloud_hpa_info.get("libvalue"),
                }
            ]

            hpa_capability = [
                {
                    'hpa-capability-id': str(uuid.uuid4()),
                    'hpa-feature': 'ovsDpdk',
                    'hpa-version': cloud_hpa_info.get("version"),
                    'architecture': cloud_hpa_info.get("arch"),
                    'hpa-feature-attributes': attributes
                },
            ]

            hpa_capabilities = {
                'hpa-capability': hpa_capability
            }

            cloud_hpa_caps = {
                'hpa_capabilities': hpa_capabilities
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
                content.update(cloud_hpa_caps)
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
            cloud_extra_info_str = viminfo.get('cloud_extra_info')
            if cloud_extra_info_str:
                cloud_extra_info = json.loads(cloud_extra_info_str)

            cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)
            ret = self._update_epa_caps(cloud_owner, cloud_region_id,
                                        cloud_extra_info)
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

