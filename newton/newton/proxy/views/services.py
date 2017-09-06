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

import re
from django.core.cache import cache

from keystoneauth1 import access
from keystoneauth1.access import service_catalog
from keystoneauth1.exceptions import HttpError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from newton.pub.exceptions import VimDriverNewtonException
from newton.requests.views.util import VimDriverUtils
from newton.pub.msapi import extsys

logger = logging.getLogger(__name__)

DEBUG=True

class Services(APIView):

    def __init__(self):
        self._logger = logger

    def head(self, request, vimid="", servicetype="", requri=""):
        self._logger.debug("Services--head::META> %s" % request.META)
        self._logger.debug("Services--head::data> %s" % request.data)
        self._logger.debug("Services--head::vimid, servicetype, requri> %s,%s,%s"
                     % (vimid, servicetype, requri))

        try:
            # prepare request resource to vim instance
            #get token:
            tmp_auth_token = request.META.get('HTTP_X_AUTH_TOKEN', None)
            if not tmp_auth_token:
                return Response(data={'error': "No X-Auth-Token found in headers"}, status=status.HTTP_401_UNAUTHORIZED)

            vim = VimDriverUtils.get_vim_info(vimid)
            #fetch the auth_state out of cache
            tmp_auth_state, metadata_catalog = VimDriverUtils.get_token_cache(vim,tmp_auth_token)
            if not tmp_auth_state:
                return Response(data={'error': "Expired X-Auth-Token found in headers"}, status=status.HTTP_401_UNAUTHORIZED)


            sess = VimDriverUtils.get_session(vim, tenantid=None, auth_state=tmp_auth_state)
            req_resource = ''
            if requri and requri != '':
                req_resource = "/" if re.match(r'//', requri) else ''+ requri

            cloud_owner, regionid = extsys.decode_vim_id(vimid)
            interface = 'public'
            service = {'service_type': servicetype,
                       'interface': interface,
                       'region_id': regionid}

            resp = sess.head(req_resource, endpoint_filter=service)
            #update token cache in case the token was required during the requests
            tmp_auth_token = VimDriverUtils.update_token_cache(vim, sess, tmp_auth_token, tmp_auth_state)
            content = resp.json()
            return Response(headers={'X-Subject-Token': tmp_auth_token}, data=content, status=resp.status_code)
            #return resp
        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, vimid="", servicetype="", requri=""):
        self._logger.debug("Services--get::META> %s" % request.META)
        self._logger.debug("Services--get::data> %s" % request.data)
        self._logger.debug("Services--get::vimid, servicetype, requri> %s,%s,%s"
                     % (vimid, servicetype, requri))
        try:
            # prepare request resource to vim instance
            #get token:
            tmp_auth_token = request.META.get('HTTP_X_AUTH_TOKEN', None)
            if not tmp_auth_token:
                return Response(data={'error': "No X-Auth-Token found in headers"}, status=status.HTTP_401_UNAUTHORIZED)

            vim = VimDriverUtils.get_vim_info(vimid)
            # fetch the auth_state out of cache
            tmp_auth_state, metadata_catalog = VimDriverUtils.get_token_cache(vim, tmp_auth_token)
            if not tmp_auth_state:
                return Response(data={'error': "Expired X-Auth-Token found in headers"}, status=status.HTTP_401_UNAUTHORIZED)

            real_prefix = None
            proxy_prefix = None
            suffix = None
            if servicetype and metadata_catalog:
#                self._logger.error("metadata_catalog:%s" % metadata_catalog)
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
                #remove the suffix from the requri to avoid duplicated suffix in real request uri later
                tmp_pattern = re.compile(suffix)
                requri = tmp_pattern.sub('', requri)

            sess = VimDriverUtils.get_session(vim, tenantid=None, auth_state=tmp_auth_state)
            req_resource = ''
            if requri and requri !=  '':
                req_resource = "/" if re.match(r'//', requri) else ''+ requri

            cloud_owner, regionid = extsys.decode_vim_id(vimid)
            interface = 'public'
            service = {'service_type': servicetype,
                       'interface': interface,
                       'region_id': regionid}

            resp = sess.get(req_resource, endpoint_filter=service)
            #update token cache in case the token was required during the requests
            tmp_auth_token = VimDriverUtils.update_token_cache(vim, sess, tmp_auth_token, tmp_auth_state)
            content = resp.json()

            #filter the resp content and replace all endpoint prefix
            tmp_content = json.dumps(content)
            tmp_pattern = re.compile(real_prefix)
            tmp_content = tmp_pattern.sub(proxy_prefix, tmp_content)
            content = json.loads(tmp_content)

            return Response(headers={'X-Subject-Token': tmp_auth_token}, data=content, status=resp.status_code)
            #return resp
        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, vimid="", servicetype="", requri=""):
        self._logger.debug("Services--post::META> %s" % request.META)
        self._logger.debug("Services--post::data> %s" % request.data)
        self._logger.debug("Services--post::vimid, servicetype,  requri> %s,%s,%s"
                     % (vimid, servicetype, requri))
        try:
            # prepare request resource to vim instance
            # get token:
            tmp_auth_token = request.META.get('HTTP_X_AUTH_TOKEN', None)
            if not tmp_auth_token:
                return Response(data={'error': "No X-Auth-Token found in headers"}, status=status.HTTP_401_UNAUTHORIZED)

            vim = VimDriverUtils.get_vim_info(vimid)
            # fetch the auth_state out of cache
            tmp_auth_state, metadata_catalog = VimDriverUtils.get_token_cache(vim, tmp_auth_token)
            if not tmp_auth_state:
                return Response(data={'error': "Expired X-Auth-Token found in headers"},
                                status=status.HTTP_401_UNAUTHORIZED)

            real_prefix = None
            proxy_prefix = None
            suffix = None
            if servicetype and metadata_catalog:
#                self._logger.error("metadata_catalog:%s" % metadata_catalog)
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
                #remove the suffix from the requri to avoid duplicated suffix in real request uri later
                tmp_pattern = re.compile(suffix)
                requri = tmp_pattern.sub('', requri)

            sess = VimDriverUtils.get_session(vim, tenantid=None, auth_state=tmp_auth_state)
            req_resource = ""
            if requri and requri != "":
                req_resource = "/" if re.match(r'//', requri) else ''+ requri

            cloud_owner, regionid = extsys.decode_vim_id(vimid)
            interface = 'public'
            service = {'service_type': servicetype,
                       'interface': interface,
                       'region_id': regionid}

            resp = sess.post(req_resource, data=json.JSONEncoder().encode(request.data),endpoint_filter=service)
            # update token cache in case the token was required during the requests
            tmp_auth_token = VimDriverUtils.update_token_cache(vim, sess, tmp_auth_token, tmp_auth_state)
            content = resp.json()

            #filter the resp content and replace all endpoint prefix
            tmp_content = json.dumps(content)
            tmp_pattern = re.compile(real_prefix)
            tmp_content = tmp_pattern.sub(proxy_prefix, tmp_content)
            content = json.loads(tmp_content)

            return Response(headers={'X-Subject-Token': tmp_auth_token}, data=content, status=resp.status_code)

        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, vimid="", servicetype="", requri=""):
        self._logger.debug("Services--put::META> %s" % request.META)
        self._logger.debug("Services--put::data> %s" % request.data)
        self._logger.debug("Services--put::vimid, servicetype, requri> %s,%s,%s"
                     % (vimid, servicetype, requri))
        try:
            # prepare request resource to vim instance
            # get token:
            tmp_auth_token = request.META.get('HTTP_X_AUTH_TOKEN', None)
            if not tmp_auth_token:
                return Response(data={'error': "No X-Auth-Token found in headers"}, status=status.HTTP_401_UNAUTHORIZED)

            vim = VimDriverUtils.get_vim_info(vimid)
            # fetch the auth_state out of cache
            tmp_auth_state, metadata_catalog = VimDriverUtils.get_token_cache(vim, tmp_auth_token)
            if not tmp_auth_state:
                return Response(data={'error': "Expired X-Auth-Token found in headers"},
                                status=status.HTTP_401_UNAUTHORIZED)

            real_prefix = None
            proxy_prefix = None
            suffix = None
            if servicetype and metadata_catalog:
#                self._logger.error("metadata_catalog:%s" % metadata_catalog)
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
                #remove the suffix from the requri to avoid duplicated suffix in real request uri later
                tmp_pattern = re.compile(suffix)
                requri = tmp_pattern.sub('', requri)

            sess = VimDriverUtils.get_session(vim, tenantid=None, auth_state=tmp_auth_state)
            req_resource = ""
            if  requri and requri != "":
                req_resource = "/" + requri

            cloud_owner, regionid = extsys.decode_vim_id(vimid)
            interface = 'public'
            service = {'service_type': servicetype,
                       'interface': interface,
                       'region_id': regionid}

            resp = sess.put(req_resource, data=json.JSONEncoder().encode(request.data),endpoint_filter=service)
            # update token cache in case the token was required during the requests
            tmp_auth_token = VimDriverUtils.update_token_cache(vim, sess, tmp_auth_token, tmp_auth_state)
            content = resp.json()

            #filter the resp content and replace all endpoint prefix
            tmp_content = json.dumps(content)
            tmp_pattern = re.compile(real_prefix)
            tmp_content = tmp_pattern.sub(proxy_prefix, tmp_content)
            content = json.loads(tmp_content)

            return Response(headers={'X-Subject-Token': tmp_auth_token}, data=content, status=resp.status_code)

        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def patch(self, request, vimid="", servicetype="", requri=""):
        self._logger.debug("Services--patch::META> %s" % request.META)
        self._logger.debug("Services--patch::data> %s" % request.data)
        self._logger.debug("Services--patch::vimid, servicetype, requri> %s,%s,%s"
                     % (vimid, servicetype, requri))
        try:
            # prepare request resource to vim instance
            # get token:
            tmp_auth_token = request.META.get('HTTP_X_AUTH_TOKEN', None)
            if not tmp_auth_token:
                return Response(data={'error': "No X-Auth-Token found in headers"}, status=status.HTTP_401_UNAUTHORIZED)

            vim = VimDriverUtils.get_vim_info(vimid)
            # fetch the auth_state out of cache
            tmp_auth_state, metadata_catalog = VimDriverUtils.get_token_cache(vim, tmp_auth_token)
            if not tmp_auth_state:
                return Response(data={'error': "Expired X-Auth-Token found in headers"},
                                status=status.HTTP_401_UNAUTHORIZED)

            real_prefix = None
            proxy_prefix = None
            suffix = None
            if servicetype and metadata_catalog:
#                self._logger.error("metadata_catalog:%s" % metadata_catalog)
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
                #remove the suffix from the requri to avoid duplicated suffix in real request uri later
                tmp_pattern = re.compile(suffix)
                requri = tmp_pattern.sub('', requri)

            sess = VimDriverUtils.get_session(vim, tenantid=None, auth_state=tmp_auth_state)
            req_resource = ""
            if requri and requri != "":
                req_resource = "/" if re.match(r'//', requri) else ''+ requri

            cloud_owner, regionid = extsys.decode_vim_id(vimid)
            interface = 'public'
            service = {'service_type': servicetype,
                       'interface': interface,
                       'region_id': regionid}

            resp = sess.patch(req_resource, data=json.JSONEncoder().encode(request.data),endpoint_filter=service)
            # update token cache in case the token was required during the requests
            tmp_auth_token = VimDriverUtils.update_token_cache(vim, sess, tmp_auth_token, tmp_auth_state)
            content = resp.json()

            #filter the resp content and replace all endpoint prefix
            tmp_content = json.dumps(content)
            tmp_pattern = re.compile(real_prefix)
            tmp_content = tmp_pattern.sub(proxy_prefix, tmp_content)
            content = json.loads(tmp_content)

            return Response(headers={'X-Subject-Token': tmp_auth_token}, data=content, status=resp.status_code)

        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, vimid="", servicetype="", requri=""):
        self._logger.debug("Services--delete::META> %s" % request.META)
        self._logger.debug("Services--delete::data> %s" % request.data)
        self._logger.debug("Services--delete::vimid, servicetype, requri> %s,%s,%s"
                     % (vimid, servicetype, requri))
        try:
            # prepare request resource to vim instance
            # get token:
            tmp_auth_token = request.META.get('HTTP_X_AUTH_TOKEN', None)
            if not tmp_auth_token:
                return Response(data={'error': "No X-Auth-Token found in headers"}, status=status.HTTP_401_UNAUTHORIZED)

            vim = VimDriverUtils.get_vim_info(vimid)
            # fetch the auth_state out of cache
            tmp_auth_state, metadata_catalog = VimDriverUtils.get_token_cache(vim, tmp_auth_token)
            if not tmp_auth_state:
                return Response(data={'error': "Expired X-Auth-Token found in headers"},
                                status=status.HTTP_401_UNAUTHORIZED)

            real_prefix = None
            proxy_prefix = None
            suffix = None
            if servicetype and metadata_catalog:
#                self._logger.error("metadata_catalog:%s" % metadata_catalog)
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
                #remove the suffix from the requri to avoid duplicated suffix in real request uri later
                tmp_pattern = re.compile(suffix)
                requri = tmp_pattern.sub('', requri)

            sess = VimDriverUtils.get_session(vim, tenantid=None, auth_state=tmp_auth_state)
            req_resource = ""
            if requri and requri != "":
                req_resource = "/" if re.match(r'//', requri) else ''+ requri

            cloud_owner, regionid = extsys.decode_vim_id(vimid)
            interface = 'public'
            service = {'service_type': servicetype,
                       'interface': interface,
                       'region_id': regionid}

            resp = sess.delete(req_resource, endpoint_filter=service)
            # update token cache in case the token was required during the requests
            tmp_auth_token = VimDriverUtils.update_token_cache(vim, sess, tmp_auth_token, tmp_auth_state)

            return Response(headers={'X-Subject-Token': tmp_auth_token}, status=resp.status_code)

        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            self._logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetTenants(Services):
    '''
    Backward compatible API for /v2.0/tenants
    '''

    def __init__(self):
        self._logger = logger

    def get(self, request, vimid="", servicetype="identity", requri='projects'):
        self._logger.debug("GetTenants--get::META> %s" % request.META)
        self._logger.debug("GetTenants--get::data> %s" % request.data)
        self._logger.debug("GetTenants--get::vimid, servicetype, requri> %s,%s,%s"
                     % (vimid, servicetype, requri))

        tmp_auth_token = request.META.get('HTTP_X_AUTH_TOKEN', None)

        resp = super(GetTenants,self).get(request, vimid, servicetype, requri)
        if resp.status_code == status.HTTP_200_OK:
            content =  resp.data
            return Response(headers={'X-Subject-Token': tmp_auth_token}, data={'tenants': content['projects'],'tenants_links':[]},
                            status=resp.status_code)
        else:
            return resp

    def head(self, request, vimid="", servicetype="", requri=""):
        return Response(data={'error': 'unsupported operation'}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, vimid="", servicetype="", requri=""):
        return Response(data={'error': 'unsupported operation'}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, vimid="", servicetype="", requri=""):
        return Response(data={'error': 'unsupported operation'}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, vimid="", servicetype="", requri=""):
        return Response(data={'error': 'unsupported operation'}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, vimid="", servicetype="", requri=""):
        return Response(data={'error': 'unsupported operation'}, status=status.HTTP_400_BAD_REQUEST)
