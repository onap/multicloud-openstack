# Copyright (c) 2017-2018 Wind River System Inc.
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

from keystoneauth1.exceptions import HttpError
import re
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from newton_base.proxy.proxy_utils import ProxyUtils
from common.exceptions import VimDriverNewtonException
from common.msapi import extsys
from newton_base.util import VimDriverUtils

logger = logging.getLogger(__name__)

# DEBUG=True


class HasValidToken(BasePermission):

    def has_permission(self, request, view):
        logger.debug("HasValidToken--has_permission::META> %s" % request.META)
        token = request.META.get('HTTP_X_AUTH_TOKEN', None)
        if token:
            state, metadata = VimDriverUtils.get_token_cache(token)
            if state:
                return True
        return False


class Services(APIView):
    permission_classes = (HasValidToken,)

    def __init__(self):
        self._logger = logger

    def _get_token(self, request):
        return request.META.get('HTTP_X_AUTH_TOKEN', None)

    def _get_resource_and_metadata(self, servicetype, metadata_catalog, requri):
        real_prefix = None
        proxy_prefix = None
        suffix = None
        if servicetype and metadata_catalog:
            metadata_catalog = json.loads(metadata_catalog)
            service_metadata = metadata_catalog.get(servicetype, None)
            if service_metadata:
                real_prefix = service_metadata['prefix']
                proxy_prefix = service_metadata['proxy_prefix']
                suffix = service_metadata['suffix']

        if not real_prefix or not proxy_prefix:
            raise VimDriverNewtonException(message="internal state error",
                                           content="invalid cached metadata",
                                           status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if requri == suffix:
            requri = None

        if suffix and requri:
            # remove the suffix from the requri to avoid duplicated suffix in real request uri later
            tmp_pattern = re.compile(suffix)
            requri = tmp_pattern.sub('', requri)

        req_resource = ''
        if requri and requri != '':
            req_resource = "/" if re.match(r'//', requri) else '' + requri
        return req_resource, metadata_catalog

    def _do_action(self, action, request, vim_id, servicetype, requri):
        tmp_auth_token = self._get_token(request)
        try:
            #special handling of compute/v2 request from APPC, temp solution for A release
            if servicetype == 'compute':
                tmp_pattern = re.compile(r'^v2/(.+)')
                requri = tmp_pattern.sub(r'v2.1/' + r'\1', requri)


            vim = VimDriverUtils.get_vim_info(vim_id)
            # fetch the auth_state out of cache
            auth_state, metadata_catalog = VimDriverUtils.get_token_cache(tmp_auth_token)
            req_resource, metadata_catalog = self._get_resource_and_metadata(servicetype, metadata_catalog, requri)
            sess = VimDriverUtils.get_session(vim, auth_state=auth_state)

            cloud_owner, regionid = extsys.decode_vim_id(vim_id)
            interface = 'public'
            service = {
                'service_type': servicetype,
                'interface': interface,
                       'region_id': regionid
            }

            querystr = VimDriverUtils.get_query_part(request)
            if querystr:
                req_resource += "?" + querystr

            self._logger.info("service " + action + " request with uri %s" % (req_resource))
            if(action == "get"):
                resp = sess.get(req_resource, endpoint_filter=service,
                                headers={"Content-Type": "application/json",
                                         "Accept": "application/json"})
            elif(action == "post"):
                resp = sess.post(req_resource, data=json.JSONEncoder().encode(request.data),
                                 endpoint_filter=service,
                                 headers={"Content-Type": "application/json",
                                          "Accept": "application/json"})
            elif(action == "put"):
                resp = sess.put(req_resource, data=json.JSONEncoder().encode(request.data),
                                endpoint_filter=service,
                                headers={"Content-Type": "application/json",
                                         "Accept": "application/json"})
            elif(action == "patch"):
                resp = sess.patch(req_resource, data=json.JSONEncoder().encode(request.data),
                                  endpoint_filter=service,
                                headers={"Content-Type": "application/json",
                                         "Accept": "application/json"})
            elif (action == "delete"):
                resp = sess.delete(req_resource, endpoint_filter=service,
                                headers={"Content-Type": "application/json",
                                         "Accept": "application/json"})
            content = resp.json() if resp.content else None
            self._logger.info("service " + action + " response status: %s" % (resp.status_code))
            self._logger.debug("service " + action + " response content: %s" % (content))

            if (action == "delete"):
                self._logger.info("RESP with status> %s" % resp.status_code)
                return Response(headers={'X-Subject-Token': tmp_auth_token}, status=resp.status_code)
            else:
                content = ProxyUtils.update_prefix(metadata_catalog, content)
                if (action == "get"):
                    if requri == '/v3/auth/catalog' and content and content.get("catalog"):
                        content['catalog'] = ProxyUtils.update_catalog_dnsaas(
                            vim_id, content['catalog'], self.proxy_prefix, vim)

                self._logger.info("RESP with status> %s" % resp.status_code)
                return Response(headers={'X-Subject-Token': tmp_auth_token},
                                data=content, status=resp.status_code)

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

    def head(self, request, vimid="", servicetype="", requri=""):
        self._logger.info("vimid, servicetype, requri> %s,%s,%s"
                     % (vimid, servicetype, requri))
        self._logger.debug("META, data> %s , %s" % (request.META, request.data))

        token = self._get_token(request)
        try:
            vim = VimDriverUtils.get_vim_info(vimid)
            auth_state, metadata_catalog = VimDriverUtils.get_token_cache(token)
            sess = VimDriverUtils.get_session(vim, auth_state=auth_state)

            req_resource = ''
            if requri and requri != '':
                req_resource = "/" if re.match(r'//', requri) else ''+ requri

            cloud_owner, regionid = extsys.decode_vim_id(vimid)
            interface = 'public'
            service = {'service_type': servicetype,
                       'interface': interface,
                       'region_id': regionid}

            self._logger.info("service head request with uri %s" % (req_resource))
            resp = sess.head(req_resource, endpoint_filter=service)
            self._logger.info("service head response status %s" % (resp.status_code))

            content = resp.json() if resp.content else None
            self._logger.debug("service head response: %s" % (content))

            return Response(headers={'X-Subject-Token': token}, data=content, status=resp.status_code)
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

    def get(self, request, vimid="", servicetype="", requri=""):
        self._logger.info("vimid, servicetype, requri> %s,%s,%s"
                     % (vimid, servicetype, requri))
        self._logger.debug("META, data> %s , %s" % (request.META, request.data))

        return self._do_action("get", request, vimid, servicetype, requri)

    def post(self, request, vimid="", servicetype="", requri=""):
        self._logger.info("vimid, servicetype, requri> %s,%s,%s"
                     % (vimid, servicetype, requri))
        self._logger.debug("META, data> %s , %s" % (request.META, request.data))

        return self._do_action("post", request, vimid, servicetype, requri)

    def put(self, request, vimid="", servicetype="", requri=""):
        self._logger.info("vimid, servicetype, requri> %s,%s,%s"
                     % (vimid, servicetype, requri))
        self._logger.debug("META, data> %s , %s" % (request.META, request.data))

        return self._do_action("put", request, vimid, servicetype, requri)

    def patch(self, request, vimid="", servicetype="", requri=""):
        self._logger.info("vimid, servicetype, requri> %s,%s,%s"
                     % (vimid, servicetype, requri))
        self._logger.debug("META, data> %s , %s" % (request.META, request.data))

        return self._do_action("patch", request, vimid, servicetype, requri)

    def delete(self, request, vimid="", servicetype="", requri=""):
        self._logger.info("vimid, servicetype, requri> %s,%s,%s"
                     % (vimid, servicetype, requri))
        self._logger.debug("META, data> %s , %s" % (request.META, request.data))

        return self._do_action("delete", request, vimid, servicetype, requri)


class GetTenants(Services):
    '''
    Backward compatible API for /v2.0/tenants
    '''

    def __init__(self):
        self._logger = logger

    def get(self, request, vimid="", servicetype="identity", requri='projects'):
        self._logger.info("vimid, servicetype, requri> %s,%s,%s"
                     % (vimid, servicetype, requri))
        self._logger.debug("META, data> %s , %s" % (request.META, request.data))

        tmp_auth_token = request.META.get('HTTP_X_AUTH_TOKEN', None)

        resp = super(GetTenants,self).get(request, vimid, servicetype, requri)
        if resp.status_code == status.HTTP_200_OK:
            content =  resp.data
            return Response(headers={'X-Subject-Token': tmp_auth_token}, data={'tenants': content['projects'],'tenants_links':[]},
                            status=resp.status_code)
        else:
            return resp

    def head(self, request, vimid="", servicetype="", requri=""):
        self._logger.warn("wrong request with vimid, servicetype, requri> %s,%s,%s"
                     % (vimid, servicetype, requri))
        return Response(data={'error': 'unsupported operation'}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, vimid="", servicetype="", requri=""):
        self._logger.warn("wrong request with vimid, servicetype, requri> %s,%s,%s"
                     % (vimid, servicetype, requri))
        return Response(data={'error': 'unsupported operation'}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, vimid="", servicetype="", requri=""):
        self._logger.warn("wrong request with vimid, servicetype, requri> %s,%s,%s"
                     % (vimid, servicetype, requri))
        return Response(data={'error': 'unsupported operation'}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, vimid="", servicetype="", requri=""):
        self._logger.warn("wrong request with vimid, servicetype, requri> %s,%s,%s"
                     % (vimid, servicetype, requri))
        return Response(data={'error': 'unsupported operation'}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, vimid="", servicetype="", requri=""):
        self._logger.warn("wrong request with vimid, servicetype, requri> %s,%s,%s"
                     % (vimid, servicetype, requri))
        return Response(data={'error': 'unsupported operation'}, status=status.HTTP_400_BAD_REQUEST)
