# Copyright (c) 2017 Wind River Systems, Inc.
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

from django.core.cache import cache

from keystoneauth1 import access
from keystoneauth1.access import service_catalog
from keystoneauth1.exceptions import HttpError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from newton.pub.config import config
from newton.pub.exceptions import VimDriverNewtonException
from newton.requests.views.util import VimDriverUtils

logger = logging.getLogger(__name__)

DEBUG=True
MULTICLOUD_PREFIX = "http://%s:%s/api/multicloud-newton/v0" %(config.MSB_SERVICE_IP, config.MSB_SERVICE_PORT)

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
#                    m = re.search(r'^http[s]*://([0-9.]+:[0-9]+)[/]*([0-9a-zA-Z/._-]*)$', endpoint_url)
                    m = re.search(r'^(http[s]?://[0-9.]+:[0-9]+)(/([0-9a-zA-Z/._-]+)$)?', endpoint_url)
                    if m:
                        real_prefix = m.group(1)
                        real_suffix = m.group(3)

                        # populate metadata_catalog
                        one_catalog['prefix'] = real_prefix
                        one_catalog['suffix'] = real_suffix if real_suffix else ''
                        one_catalog['proxy_prefix'] = multicould_namespace + "/%s" % vimid + "/" + item["type"]

                        endpoint_url = multicould_namespace + "/%s" % vimid + "/" + item["type"]

                        if real_suffix:
                            endpoint_url += "/" + real_suffix

                        if item["type"] == "identity":
                            endpoint_url = multicould_namespace + "/%s/identity/v3" % vimid

#                        endpoint["url"] = re.sub(r"^http([s]*)://([0-9.]+):([0-9]+)",
#                                                 multicould_namespace + "/%s/" % vimid + item["type"],
#                                                 endpoint["url"])


                    endpoint["url"] = endpoint_url
                item['endpoints'].append( endpoint )

        return catalog, metadata_catalog
    else:
        return None
    pass




class Tokens(APIView):
    service = {'service_type': 'identity',
               'interface': 'public'}

    def __init__(self):
        self.proxy_prefix = MULTICLOUD_PREFIX

    def post(self, request, vimid=""):
        logger.debug("identityV3--post::> %s" % request.data)
        sess = None
        resp = None
        resp_body = None
        try:
            # prepare request resource to vim instance
            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim)

            tmp_auth_state = VimDriverUtils.get_auth_state(vim, sess)
            tmp_auth_info = json.loads(tmp_auth_state)
            tmp_auth_token = tmp_auth_info['auth_token']
            tmp_auth_data = tmp_auth_info['body']

            #store the auth_state, redis/memcached
            #set expiring in 1 hour

            #update the catalog
            tmp_auth_data['token']['catalog'], tmp_metadata_catalog = update_catalog(vimid, tmp_auth_data['token']['catalog'], self.proxy_prefix)
            VimDriverUtils.update_token_cache(vim, sess, tmp_auth_token, tmp_auth_state, json.dumps(tmp_metadata_catalog))

            resp = Response(headers={'X-Subject-Token': tmp_auth_token}, data=tmp_auth_data, status=status.HTTP_201_CREATED)
            return resp
        except VimDriverNewtonException as e:

            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            logger.error(traceback.format_exc())

            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        pass


class Catalog(APIView):

    service = {'service_type': 'identity',
               'interface': 'public'}

    def __init__(self):
        self.proxy_prefix = MULTICLOUD_PREFIX

    def get(self, request, vimid=""):
        logger.debug("Catalog--get::data> %s" % request.data)
#        logger.debug("Catalog--get::META> %s" % request.META)
        try:
            # prepare request resource to vim instance
            #get token:
            tmp_auth_token = request.META.get('HTTP_X_AUTH_TOKEN', None)
            if not tmp_auth_token:
                return Response(data={'error': "No X-Auth-Token found in headers"}, status=status.HTTP_401_UNAUTHORIZED)

            vim = VimDriverUtils.get_vim_info(vimid)
            #fetch the auth_state out of cache
            tmp_auth_state, metadata_catalog = VimDriverUtils.get_token_cache(vim, tmp_auth_token)
            if not tmp_auth_state:
                return Response(data={'error': "Expired X-Auth-Token found in headers"}, status=status.HTTP_401_UNAUTHORIZED)

            sess = VimDriverUtils.get_session(vim, auth_state=tmp_auth_state)
            req_resource = "/auth/catalog"

            resp = sess.get(req_resource, endpoint_filter=self.service)
            #update token cache in case the token was required during the requests
            tmp_auth_token = VimDriverUtils.update_token_cache(vim, sess, tmp_auth_token, tmp_auth_state)

            content = resp.json()
            tmp_auth_catalog = content['catalog']
            update_catalog(vimid, tmp_auth_catalog, self.proxy_prefix)

            return Response(headers={'X-Subject-Token':tmp_auth_token}, data={'catalog': tmp_auth_catalog}, status=resp.status_code)
        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        pass
