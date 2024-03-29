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

from django.core.cache import cache

from keystoneauth1 import access
from keystoneauth1.access import service_catalog
from keystoneauth1.exceptions import HttpError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import VimDriverNewtonException
from newton_base.util import VimDriverUtils
from newton_base.proxy.proxy_utils import ProxyUtils

logger = logging.getLogger(__name__)

# DEBUG=True

v3_version_detail = {
    "version": {
        "status": "stable",
        "updated": "2014-04-17T00:00:00Z",
        "media-types": [
            {
                "base": "application/json",
                "type": "application/vnd.openstack.identity-v3+json"
            }
        ],
        "id": "v3",
        "links": [
        ]
    }
}

class Tokens(APIView):
    service = {'service_type': 'identity',
               'interface': 'public'}

    def __init__(self):
        self.proxy_prefix = "multicloud"
        self._logger = logger

    def get(self, request, vimid=""):
        self._logger.info("vimid> %s" % vimid)
        self._logger.debug("META> %s" % request.META)
        self._logger.debug("data> %s" % request.data)

        self._logger.info("RESP with status> %s" % status.HTTP_200_OK)

        # compose the links
        v3_version_detail["version"]["links"] = [{
                "href": request.META.get("REQUEST_URI", ""),
                "rel": "self"
            }]
        return Response(data=v3_version_detail, status=status.HTTP_200_OK)

    def post(self, request, vimid=""):
        self._logger.info("vimid> %s" % vimid)
        self._logger.debug("META> %s" % request.META)
        self._logger.debug("data> %s" % request.data)

        sess = None
        resp = None
        resp_body = None
        try:
            tenant_name = request.data.get("tenant_name")
            tenant_id = request.data.get("tenant_id")

            #backward support for keystone v2.0 API
            if not tenant_name and request.data.get("auth"):
                tenant_name = request.data["auth"].get("tenantName")
                tenant_id = request.data["auth"].get("tenantId")

            #keystone v3 API
            if not tenant_name and request.data.get("auth") \
                    and request.data["auth"].get("scope")\
                    and request.data["auth"]["scope"].get("project"):
                if request.data["auth"]["scope"]["project"].get("name"):
                    tenant_name = request.data["auth"]["scope"]["project"].get("name")
                else:
                    tenant_id = request.data["auth"]["scope"]["project"].get("id")

            # Get the specified tenant id
            specified_project_idorname = request.META.get("Project", None)

            # prepare request resource to vim instance
            vim = VimDriverUtils.get_vim_info(vimid)
            sess = None
            if specified_project_idorname:
                try:
                    # check if specified with tenant id
                    sess = VimDriverUtils.get_session(
                        vim, tenant_name=None,
                        tenant_id=specified_project_idorname
                    )
                except Exception as e:
                    pass

                if not sess:
                    try:
                        # check if specified with tenant name
                        sess = VimDriverUtils.get_session(
                            vim, tenant_name=specified_project_idorname,
                            tenant_id=None
                        )
                    except Exception as e:
                        pass

            if not sess:
                sess = VimDriverUtils.get_session(
                    vim, tenant_name=tenant_name, tenant_id=tenant_id)

            #tmp_auth_state = VimDriverUtils.get_auth_state(vim, sess)
            tmp_auth_state = VimDriverUtils.get_auth_state(sess)
            tmp_auth_info = json.loads(tmp_auth_state)
            tmp_auth_token = tmp_auth_info['auth_token']
            tmp_auth_data = tmp_auth_info['body']

            #store the auth_state, redis/memcached
            #set expiring in 1 hour

            #update the catalog
            tmp_auth_data['token']['catalog'], tmp_metadata_catalog = ProxyUtils.update_catalog(
                vimid, tmp_auth_data['token']['catalog'], self.proxy_prefix)

            VimDriverUtils.update_token_cache(
                tmp_auth_token, tmp_auth_state, json.dumps(tmp_metadata_catalog))

            tmp_auth_data['token']['catalog'] = ProxyUtils.update_catalog_dnsaas(
                vimid,tmp_auth_data['token']['catalog'], self.proxy_prefix, vim)

            resp = Response(headers={'X-Subject-Token': tmp_auth_token},
                            data=tmp_auth_data, status=status.HTTP_201_CREATED)

            self._logger.info("RESP with status> %s" % status.HTTP_201_CREATED)

            return resp
        except VimDriverNewtonException as e:

            self._logger.error("Plugin exception> status:%s,error:%s"
                                  % (e.status_code, e.content))
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            self._logger.error(traceback.format_exc())

            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

v2_version_detail = {
    "version": {
        "status": "deprecated",
        "updated": "2016-08-04T00:00:00Z",
        "media-types": [
            {
                "base": "application/json",
                "type": "application/vnd.openstack.identity-v2.0+json"
            }
        ],
        "id": "v2.0",
        "links": [
        ],
        "type": "text/html",
        "rel": "describedby"

    }
}

class TokensV2(Tokens):
    '''
    Backward compatible API for /v2.0/tokens
    '''

    def __init__(self):
        self.proxy_prefix = "multicloud"
        self._logger = logger

    def get(self, request, vimid=""):
        self._logger.info("vimid> %s" % vimid)
        self._logger.debug("TokensV2--get::META> %s" % request.META)

        self._logger.info("RESP with status> %s" % status.HTTP_200_OK)
        # compose the links
        v2_version_detail["version"]["links"] = [{
                "href": request.META.get("REQUEST_URI", ""),
                "rel": "self"
            }]
        return Response(data=v2_version_detail, status=status.HTTP_200_OK)

    def post(self, request, vimid=""):
        self._logger.info("vimid > %s" % vimid)
        self._logger.debug("META> %s" % request.META)
        self._logger.debug("data> %s" % request.data)


        try:
            resp = super(TokensV2,self).post(request, vimid)
            # self._logger.debug("Token(v3)returns> headers:%s, data:%s" % (resp._headers, resp.data))
            if resp.status_code == status.HTTP_201_CREATED:
                v3_content =  resp.data
                v3_token = v3_content['token']

                #convert catalog
                v2_catalog = []
                for v3_catalog in v3_token['catalog']:
                    v2_catalog1 = {
                        "type": v3_catalog["type"],
                        "name": v3_catalog["name"],
                        "endpoints": []
                    }

                    #convert endpoints
                    v2_catalog1_endpoints = None
                    for v3_endpoint in v3_catalog['endpoints']:
                        v2_catalog1_endpoints = {
                            "id": v3_endpoint['id'],
                            "region":v3_endpoint['region'],
                            "region_name": v3_endpoint['region_id'],
                            'interface':v3_endpoint['interface']
                        }
                        if v3_endpoint['interface'] == 'public':
                            v2_catalog1_endpoints['publicURL'] = v3_endpoint['url']
                        elif v3_endpoint['interface'] == 'admin':
                            v2_catalog1_endpoints['adminURL'] = v3_endpoint['url']
                        elif v3_endpoint['interface'] == 'internal':
                            v2_catalog1_endpoints['internalURL'] = v3_endpoint['url']

                        if v2_catalog1_endpoints:
                            v2_catalog1['endpoints'].append(v2_catalog1_endpoints)

                    v2_catalog.append(v2_catalog1)


                #conversion between v3 tokens response and v2.0 tokens response
                v3_token["project"]['enabled'] = 'true'
                v2_content = {
                    "access": {
                        "token": {
                            "id" : resp.get('X-Subject-Token', None),
                            "issued_at": v3_token["issued_at"],
                            "expires" : v3_token["expires_at"],
                            "tenant" : v3_token["project"],
                        },
                        "serviceCatalog": v2_catalog,
                        "user": v3_token["user"],
                    }
                }

                self._logger.info("RESP with status> %s" % status.HTTP_200_OK)
                return Response(data=v2_content,
                                status=status.HTTP_200_OK \
                                    if resp.status_code==status.HTTP_201_CREATED \
                                    else resp.status_code)

            else:
                self._logger.info("RESP with status> %s" % resp.status_code)
                return resp
        except VimDriverNewtonException as e:

            self._logger.error("Plugin exception> status:%s,error:%s"
                                  % (e.status_code, e.content))
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            self._logger.error(traceback.format_exc())

            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
