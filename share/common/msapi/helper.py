# Copyright (c) 2017-2018 Wind River Systems, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

import json
import logging
import re

from common.exceptions import VimDriverNewtonException
from common.utils import restcall

from rest_framework import status

logger = logging.getLogger(__name__)


class Helper(object):

    @staticmethod
    def MultiCloudIdentityHelper(multicloud_api_prefix, cloud_owner, cloud_region_id, uri, data={}, header=''):
        auth_api_url_format = "/{f_cloudowner}/{f_cloudregionid}/identity{f_uri}"
        auth_api_url = auth_api_url_format.format(f_cloudowner=cloud_owner,
                                                  f_cloudregionid=cloud_region_id,
                                                  f_uri=uri)
        extra_headers = header
        ret = restcall._call_req(multicloud_api_prefix, "", "", 0, auth_api_url, "POST", extra_headers, json.dumps(data))
        if ret[0] == 0 and ret[1]:
            content = json.JSONDecoder().decode(ret[1])
            ret[1] = content
        return ret

    # The consumer of this api must be attaching to the same management network of multicloud,
    # The constraints comes from the returned catalog endpoint url e.g. "http://10.0.14.1:80/api/multicloud-titaniumcloud/v0/pod25_RegionOne/identity/v3"
    @staticmethod
    def MultiCloudServiceHelper(cloud_owner, cloud_region_id, v2_token_resp_json, service_type, uri, data=None, method="GET",):
        # get endpoint from token response
        token = v2_token_resp_json["access"]["token"]["id"]
        catalogs = v2_token_resp_json["access"]["serviceCatalog"]
        for catalog in catalogs:
            if catalog['type'] == service_type:
                # now we have endpoint
                endpoint_url = catalog['endpoints'][0]['publicURL']
                extra_headers = {'X-Auth-Token': token}
                ret = restcall._call_req(endpoint_url, "", "", 0, uri, method, extra_headers, json.dumps(data) if data else "")
                if ret[0] == 0 and ret[1]:
                    content = json.JSONDecoder().decode(ret[1])
                    ret[1] = content
                return ret
        return [1, None, status.HTTP_404_NOT_FOUND] # return resource not found in case no type found