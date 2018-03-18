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

from django.conf import settings

from newton_base.registration import registration as newton_registration
from newton.requests.views.flavor import Flavors

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

                if config.AAI_SCHEMA_VERSION == "v13":
                    extraResp = Flavors._get_flavor_extra_specs(session, flavor['id'])
                    extraContent = extraResp.json()
                    hpa_capabilities = self._get_hpa_capabilities(vimid, flavor,
                                                                  extraContent["extra_specs"])
                    flavor_info['hpa_capabilities'] = hpa_capabilities

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

    def _get_hpa_capabilities(self, vimid, flavor, extra_specs):
        """Convert flavor information to HPA capabilities for AAI"""
        cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)

        json_data = open(hpa.json).read()
        hpa_dict = json.loads(json_data)

        capabilities = []

        # Basic Capabilities
        if set(hpa_dict['basicCapabilities']['hpa-attributes']).intersection(flavor):
            capability = hpa_dict['basicCapabilities']['info']
            capability['hpa-capability-id'] = str(uuid.uuid4())
            capability['hpa-feature-attributes'] = self._get_capability_attributes(
                                                       flavor,
                                                       hpa_dict['basicCapabilities']['hpa-attributes'])
            capabilities.append(capability)

        # Local Storage
        if set(hpa_dict['localStorage']['hpa-attributes']).intersection(flavor):
            capability = hpa_dict['localStorage']['info']
            capability['hpa-capability-id'] = str(uuid.uuid4())
            capability['hpa-feature-attributes'] = self._get_capability_attributes(
                                                       flavor,
                                                       hpa_dict['localStorage']['hpa-attributes'])
            capabilities.append(capability)

        # CPU Topology
        if set(hpa_dict['cpuTopology']['hpa-attributes']).intersection(extra_specs):
            capability = hpa_dict['cpuTopology']['info']
            capability['hpa-capability-id'] = str(uuid.uuid4())
            capability['hpa-features-attributes'] = self._get_capability_attributes(
                                                        extra_specs,
                                                        hpa_dict['cpuTopology']['hpa-attributes'])
            capabilities.append(capability)

        # CPU Pinning
        if set(hpa_dict['cpuTopology']['hpa-attributes']).intersection(extra_specs):
            capability = hpa_dict['cpuPinning']['info']
            capability['hpa-capability-id'] = str(uuid.uuid4())
            capability['hpa-features-attributes'] = self._get_capability_attributes(
                                                        extra_specs,
                                                        hpa_dict['cpuTopology']['hpa-attributes'])
            capabilities.append(capability)

        # Huge Pages
        if set(hpa_dict['hugePages']['hpa-attributes']).intersection(extra_specs):
            capability = hpa_dict['hugePages']['info']
            capability['hpa-capability-id'] = str(uuid.uuid4())
            capability['hpa-features-attributes'] = self._get_capability_attributes(
                                                        extra_specs,
                                                        hpa_dict['hugePages']['hpa-attributes'])
            capabilities.append(capability)

        # NUMA
        if "hw:numa_nodes" in extra_specs:
            capability = hpa_dict['numa']['info']
            capability['hpa-capability-id'] = str(uuid.uuid4())
            # NUMA nodes are a special case and can't use the generic get attrs function
            attributes = []
            attributes.append({
                'hpa-attribute-key': hpa_dict['numa']['hpa-attributes']['hw:numa_nodes']['key'],
                'hpa-attribute-value': "{\"value\":\"{0}\"}".format(extra_specs['hw:numa_nodes'])
            })
            for spec in extra_specs:
                if spec.startswith('hw:numa_cpus'):
                    cpu_num = spec.split(":")[-1]
                    attributes.append({
                        'hpa-attribute-key': 'numaCpu-' + cpu_num,
                        'hpa-attribute-value': "{\"value\":\"{0}\"}".format(extra_specs[spec])
                    })
                elif spec.startswith('hw:numa_mem'):
                    mem_num = spec.split(":")[-1]
                    attributes.append({
                        'hpa-attribute-key': 'numaMem-' + mem_num,
                        'hpa-attribute-value': "{\"value\":\"{0}\",\"unit\":\"{1}\"}".format(extra_specs[spec],
                                                                                             "GB")
                    })
            capability['hpa-features-attributes'] = attributes
            capabilities.append(capability)

        # PCIe Passthrough
        pci_devices = [spec for spec in extra_specs if spec.startswith("pci_passthrough:alias")]
        for device in pci_devices:
            capability = hpa_dict['pciePassthrough']['info']
            capability['hpa-capability-id'] = str(uuid.uuid4())
            # device will be in the form pci_passthrough:alias=ALIAS:COUNT,
            # ALIAS is expected to be in the form <NAME>-<VENDOR_ID>-<DEVICE_ID>
            device_info = device.split("=")[-1].split(":")
            count = device_info[-1]
            vendor_id = device_info.split(":")[0].split("-")[1]
            device_id = device_info.split(":")[0].split("-")[2]

            attributes = [
                {
                    'hpa-attribute-key': 'pciCount',
                    'hpa-attribute-value': "{\"value\":\"{0}\"}".format(count)
                },
                {
                    'hpa-attribute-key': 'pciVendorId',
                    'hpa-attribute-value': "{\"value\":\"{0}\"}".format(vendor_id)
                },
                {
                    'hpa-attribute-key': 'pciDeviceId',
                    'hpa-attribute-value': "{\"value\":\"{0}\"}".format(device_id)
                }
            ]

            capability['hpa-features-attributes'] = attributes
            capabilities.append(capability)

        return capabilities

    def _get_capability_attributes(self, cloud_info, attributes):
        result = []
        for attr in attributes:
            if attr in cloud_info:
                attribute = {'hpa-attribute-key': attributes[attr][key]}
                if attributes[attr][unit]:
                    attribute['hpa-attribute-value'] = (
                        "{\"value\":\"{0}\",\"unit\":\"{1}\"").format(cloud_info[attr],
                                                                      hpa_dict[attr][unit])
                else:
                    attribute['hpa-attribute-value'] = (
                        "{\"value\": \"{0}\"}").format(cloud_info[attr])

                result.append(attribute)
        return result
