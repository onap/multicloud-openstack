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
import traceback
import re
import uuid

from rest_framework import status

from newton.pub.exceptions import VimDriverNewtonException

logger = logging.getLogger(__name__)

DEBUG=True
#MULTICLOUD_PREFIX = "http://%s:%s/api/multicloud-newton/v0" %(config.MSB_SERVICE_IP, config.MSB_SERVICE_PORT)

class ProxyUtils(object):

    @staticmethod
    def update_prefix(metadata_catalog, content):
        '''match the longgest prefix and replace it'''

        if not content:
            return content

        for (servicetype, service_metadata) in metadata_catalog.items():
            real_prefix = service_metadata['prefix']
            proxy_prefix = service_metadata['proxy_prefix']

            if content:
                # filter the resp content and replace all endpoint prefix
                tmp_content = json.dumps(content)
                tmp_pattern = re.compile(real_prefix+r'([^:])')
                tmp_content = tmp_pattern.sub(proxy_prefix+r'\1', tmp_content)
                content = json.loads(tmp_content)

        return content

    @staticmethod
    def update_catalog(vimid, catalog, multicould_namespace):
        '''
        replace the orignal endpoints with multicloud's
        return the catalog with updated endpoints, and also another catalog with prefix and suffix of each endpoint
        :param vimid:
        :param catalog: service catalog to be updated
        :param multicould_namespace: multicloud namespace prefix to replace the real one in catalog endpoints url
        :return:updated catalog, and metadata_catalog looks like:
        {
            'compute': {
                'prefix': 'http://ip:port',
                'proxy_prefix': 'http://another_ip: another_port',
                'suffix': 'v2.1/53a4ab9015c84ee892e46d294f3b8b2d',
            },
            'network': {
                'prefix': 'http://ip:port',
                'proxy_prefix': 'http://another_ip: another_port',
                'suffix': '',
            },
        }
        '''

        metadata_catalog = {}
        if catalog:
            # filter and replace endpoints of catalogs
            for item in catalog:
                one_catalog = {}
                metadata_catalog[item['type']] = one_catalog

                endpoints = item['endpoints']
                item['endpoints']=[]
                for endpoint in endpoints:
                    interface = endpoint.get('interface', None)
                    if interface != 'public':
                        continue
    #                elif item["type"] == "identity":
    #                    endpoint["url"] = multicould_namespace + "/%s/identity/v3" % vimid
                    else:
                        # replace the endpoint with MultiCloud's proxy
                        import re
                        endpoint_url = endpoint["url"]
                        real_prefix = None
                        real_suffix = None
                        m = re.search(r'^(http[s]?://[0-9.]+:[0-9]+)(/([0-9a-zA-Z/._-]+)$)?', endpoint_url)
                        if not m:
                            m = re.search(r'^(http[s]?://[0-9.]+)(/([0-9a-zA-Z/._-]+)$)?', endpoint_url)
                        if m:
                            real_prefix = m.group(1)
                            real_suffix = m.group(3)

                        if real_prefix:
                            # populate metadata_catalog
                            one_catalog['prefix'] = real_prefix
                            one_catalog['suffix'] = real_suffix if real_suffix else ''
                            one_catalog['proxy_prefix'] = multicould_namespace + "/%s" % vimid

                            endpoint_url = multicould_namespace + "/%s" % vimid

                            tmp_pattern = re.compile(item["type"])
                            if not real_suffix or not re.match(tmp_pattern, real_suffix):
                                one_catalog['proxy_prefix'] += "/" + item["type"]
                                endpoint_url += '/' + item["type"]

                            if real_suffix:
                                endpoint_url += "/" + real_suffix

                            if item["type"] == "identity":
                                endpoint_url = multicould_namespace + "/%s/identity/v3" % vimid

                        else:
                            #something wrong
                            pass

                        endpoint["url"] = endpoint_url
                    item['endpoints'].append( endpoint )

            return catalog, metadata_catalog
        else:
            return None


    @staticmethod
    def update_catalog_dnsaas(vimid, catalog, multicould_namespace, viminfo):
        '''
        append DNSaaS delegate endpoints to catalog
        :param vimid:
        :param catalog: service catalog to be updated
        :param multicould_namespace: multicloud namespace prefix to replace the real one in catalog endpoints url
        :param viminfo: vim information
        :return:updated catalog
        '''

        try:
            cloud_dns_delegate_info = None
            cloud_extra_info_str = viminfo.get('cloud_extra_info')
            if cloud_extra_info_str:
                cloud_extra_info = json.loads(cloud_extra_info_str)
                cloud_dns_delegate_info = cloud_extra_info.get("dns-delegate")

            if not cloud_dns_delegate_info\
                    or not cloud_dns_delegate_info.get("cloud-owner") \
                    or not cloud_dns_delegate_info.get("cloud-region-id"):
                #DNSaaS deleget was not configured yet
                return catalog

            dns_catalog = {
                "name":"dns-delegate",
                "type":"dns",
                "id": str(uuid.uuid1()),
                "endpoints": [{
                    "interface": "public",
                    "region": cloud_dns_delegate_info.get("cloud-region-id"),
                    "region_id": cloud_dns_delegate_info.get("cloud-region-id"),
                    "id": str(uuid.uuid1()),
                    "url": multicould_namespace + "/%s/dns-delegate" % vimid,
                }]
            }
            catalog.append(dns_catalog)

            return catalog

        except Exception as e:
            logger.error(traceback.format_exc())
            return catalog


#    @staticmethod
#    def update_dnsaas_project_id(content, new_project_id):
#        '''
#        update project id in DNSaaS delegate content
#        '''
#        try:
#            if content:
#                # filter the resp content and replace all endpoint prefix
#                tmp_content = json.dumps(content)
#                tmp_pattern = re.compile(r'(^.*)"project_id"\s*:\s*"' + r'[\w-]+'+r'"(.*$)')
#                part1 = tmp_pattern.sub(r'\1', tmp_content)
#                part2 = tmp_pattern.sub(r'"project_id":"'+new_project_id +r'"\2', tmp_content)
#                #logger.debug("jsonstr:%s,part1:%s,part2:%s"%(tmp_content,part1,part2))
#                content = json.loads(part1+part2)
#            return content
#        except Exception as e:
#            logger.error(traceback.format_exc())
#            return content
