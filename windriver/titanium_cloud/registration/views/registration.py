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
                req_resouce = "/flavors/%s/os-extra_specs" % flavor['id']
                extraResp = self._get_list_resources(req_resouce, "compute", session, viminfo, vimid, "extra_specs")

                hpa_capabilities = self._get_hpa_capabilities(flavor, extraResp)
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

    def _get_hpa_capabilities(self, flavor, extra_specs):
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

        return hpa_caps

    def _get_hpa_basic_capabilities(self, flavor):
        basic_capability = {}
        feature_uuid = uuid.uuid4()

        basic_capability['hpaCapabilityID'] = str(feature_uuid)
        basic_capability['hpaFeature'] = 'basicCapabilities'
        basic_capability['hardwareArchitecture'] = 'generic'
        basic_capability['version'] = 'v1'

        basic_capability['attributes'] = []
        basic_capability['attributes'].append({'hpa-attribute-key': 'numVirtualCpu',
                                               'hpa-attribute-value':{'value': str(flavor['vcpus']) }})
        basic_capability['attributes'].append({'hpa-attribute-key':'virtualMemSize',
                                               'hpa-attribute-value': {'value':str(flavor['ram']), 'unit':'MB'}})

        return basic_capability

    def _get_cpupining_capabilities(self, extra_specs):
        cpupining_capability = {}
        feature_uuid = uuid.uuid4()

        if extra_specs.has_key('hw:cpu_policy') or extra_specs.has_key('hw:cpu_thread_policy'):
            cpupining_capability['hpaCapabilityID'] = str(feature_uuid)
            cpupining_capability['hpaFeature'] = 'cpuPining'
            cpupining_capability['hardwareArchitecture'] = 'generic'
            cpupining_capability['version'] = 'v1'

            cpupining_capability['attributes'] = []
            if extra_specs.has_key('hw:cpu_thread_policy'):
                cpupining_capability['attributes'].append({'hpa-attribute-key': 'logicalCpuThreadPinningPolicy',
                                                           'hpa-attribute-value':{'value': str(extra_specs['hw:cpu_thread_policy'])}})
            if extra_specs.has_key('hw:cpu_policy'):
                cpupining_capability['attributes'].append({'hpa-attribute-key':'logicalCpuPinningPolicy',
                                                           'hpa-attribute-value': {'value':str(extra_specs['hw:cpu_policy'])}})

        return cpupining_capability

    def _get_cputopology_capabilities(self, extra_specs):
        cputopology_capability = {}
        feature_uuid = uuid.uuid4()

        if extra_specs.has_key('hw:cpu_sockets') or extra_specs.has_key('hw:cpu_cores') or extra_specs.has_key('hw:cpu_threads'):
            cputopology_capability['hpaCapabilityID'] = str(feature_uuid)
            cputopology_capability['hpaFeature'] = 'cpuTopology'
            cputopology_capability['hardwareArchitecture'] = 'generic'
            cputopology_capability['version'] = 'v1'

            cputopology_capability['attributes'] = []
            if extra_specs.has_key('hw:cpu_sockets'):
                cputopology_capability['attributes'].append({'hpa-attribute-key': 'numCpuSockets',
                                                             'hpa-attribute-value':{'value': str(extra_specs['hw:cpu_sockets'])}})
            if extra_specs.has_key('hw:cpu_cores'):
                cputopology_capability['attributes'].append({'hpa-attribute-key': 'numCpuCores',
                                                             'hpa-attribute-value':{'value': str(extra_specs['hw:cpu_cores'])}})
            if extra_specs.has_key('hw:cpu_threads'):
                cputopology_capability['attributes'].append({'hpa-attribute-key': 'numCpuThreads',
                                                             'hpa-attribute-value':{'value': str(extra_specs['hw:cpu_threads'])}})

        return cputopology_capability

