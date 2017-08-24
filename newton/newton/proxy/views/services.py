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

from newton.pub.exceptions import VimDriverNewtonException
from newton.requests.views.util import VimDriverUtils

logger = logging.getLogger(__name__)

DEBUG=True

class Services(APIView):

    def head(self, request, vimid="", servicetype="", regionid="", interface="", requri=""):
        logger.debug("Services--head::data> %s" % request.data)
        logger.debug("Services--head::vimid, servicetype, regionid, interface, requri> %s,%s,%s,%s,%s"
                     % (vimid, servicetype, regionid, interface, requri))
        try:
            # prepare request resource to vim instance
            #get token:
            tmp_auth_token = request.META.get('HTTP_X_AUTH_TOKEN', None)
            if not tmp_auth_token:
                return Response(data={'error': "No X-Auth-Token found in headers"}, status=status.HTTP_401_UNAUTHORIZED)

            #fetch the auth_state out of cache
            tmp_auth_state = cache.get(tmp_auth_token)
            if not tmp_auth_state:
                return Response(data={'error': "Expired X-Auth-Token found in headers"}, status=status.HTTP_401_UNAUTHORIZED)

            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid=None, auth_state=tmp_auth_state)
            req_resource = "/"+requri

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
            logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, vimid="", servicetype="", regionid="", interface="", requri=""):
        logger.debug("Services--get::data> %s" % request.data)
        logger.debug("Services--get::vimid, servicetype, regionid, interface, requri> %s,%s,%s,%s,%s"
                     % (vimid, servicetype, regionid, interface, requri))
        try:
            # prepare request resource to vim instance
            #get token:
            tmp_auth_token = request.META.get('HTTP_X_AUTH_TOKEN', None)
            if not tmp_auth_token:
                return Response(data={'error': "No X-Auth-Token found in headers"}, status=status.HTTP_401_UNAUTHORIZED)

            #fetch the auth_state out of cache
            tmp_auth_state = cache.get(tmp_auth_token)
            if not tmp_auth_state:
                return Response(data={'error': "Expired X-Auth-Token found in headers"}, status=status.HTTP_401_UNAUTHORIZED)

            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid=None, auth_state=tmp_auth_state)
            req_resource = "/"+requri

            service = {'service_type': servicetype,
                       'interface': interface,
                       'region_id': regionid}

            resp = sess.get(req_resource, endpoint_filter=service)
            #update token cache in case the token was required during the requests
            tmp_auth_token = VimDriverUtils.update_token_cache(vim, sess, tmp_auth_token, tmp_auth_state)
            content = resp.json()
            return Response(headers={'X-Subject-Token': tmp_auth_token}, data=content, status=resp.status_code)
            #return resp
        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, vimid="", servicetype="", regionid="", interface="", requri=""):
        logger.debug("Services--post::data> %s" % request.data)
        logger.debug("Services--post::vimid, servicetype, regionid, interface, requri> %s,%s,%s,%s,%s"
                     % (vimid, servicetype, regionid, interface, requri))
        try:
            # prepare request resource to vim instance
            # get token:
            tmp_auth_token = request.META.get('HTTP_X_AUTH_TOKEN', None)
            if not tmp_auth_token:
                return Response(data={'error': "No X-Auth-Token found in headers"}, status=status.HTTP_401_UNAUTHORIZED)

            # fetch the auth_state out of cache
            tmp_auth_state = cache.get(tmp_auth_token)
            if not tmp_auth_state:
                return Response(data={'error': "Expired X-Auth-Token found in headers"},
                                status=status.HTTP_401_UNAUTHORIZED)

            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid=None, auth_state=tmp_auth_state)
            req_resource = ""
            if requri != "":
                req_resource = "/" + requri

            service = {'service_type': servicetype,
                       'interface': interface,
                       'region_id': regionid}

            resp = sess.post(req_resource, data=json.JSONEncoder().encode(request.data),endpoint_filter=service)
            # update token cache in case the token was required during the requests
            tmp_auth_token = VimDriverUtils.update_token_cache(vim, sess, tmp_auth_token, tmp_auth_state)
            content = resp.json()
            return Response(headers={'X-Subject-Token': tmp_auth_token}, data=content, status=resp.status_code)

        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, vimid="", servicetype="", regionid="", interface="", requri=""):
        logger.debug("Services--put::data> %s" % request.data)
        logger.debug("Services--put::vimid, servicetype, regionid, interface, requri> %s,%s,%s,%s,%s"
                     % (vimid, servicetype, regionid, interface, requri))
        try:
            # prepare request resource to vim instance
            # get token:
            tmp_auth_token = request.META.get('HTTP_X_AUTH_TOKEN', None)
            if not tmp_auth_token:
                return Response(data={'error': "No X-Auth-Token found in headers"}, status=status.HTTP_401_UNAUTHORIZED)

            # fetch the auth_state out of cache
            tmp_auth_state = cache.get(tmp_auth_token)
            if not tmp_auth_state:
                return Response(data={'error': "Expired X-Auth-Token found in headers"},
                                status=status.HTTP_401_UNAUTHORIZED)

            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid=None, auth_state=tmp_auth_state)
            req_resource = ""
            if requri != "":
                req_resource = "/" + requri

            service = {'service_type': servicetype,
                       'interface': interface,
                       'region_id': regionid}

            resp = sess.put(req_resource, data=json.JSONEncoder().encode(request.data),endpoint_filter=service)
            # update token cache in case the token was required during the requests
            tmp_auth_token = VimDriverUtils.update_token_cache(vim, sess, tmp_auth_token, tmp_auth_state)
            content = resp.json()
            return Response(headers={'X-Subject-Token': tmp_auth_token}, data=content, status=resp.status_code)

        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def patch(self, request, vimid="", servicetype="", regionid="", interface="", requri=""):
        logger.debug("Services--patch::data> %s" % request.data)
        logger.debug("Services--patch::vimid, servicetype, regionid, interface, requri> %s,%s,%s,%s,%s"
                     % (vimid, servicetype, regionid, interface, requri))
        try:
            # prepare request resource to vim instance
            # get token:
            tmp_auth_token = request.META.get('HTTP_X_AUTH_TOKEN', None)
            if not tmp_auth_token:
                return Response(data={'error': "No X-Auth-Token found in headers"}, status=status.HTTP_401_UNAUTHORIZED)

            # fetch the auth_state out of cache
            tmp_auth_state = cache.get(tmp_auth_token)
            if not tmp_auth_state:
                return Response(data={'error': "Expired X-Auth-Token found in headers"},
                                status=status.HTTP_401_UNAUTHORIZED)

            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid=None, auth_state=tmp_auth_state)
            req_resource = ""
            if requri != "":
                req_resource = "/" + requri

            service = {'service_type': servicetype,
                       'interface': interface,
                       'region_id': regionid}

            resp = sess.patch(req_resource, data=json.JSONEncoder().encode(request.data),endpoint_filter=service)
            # update token cache in case the token was required during the requests
            tmp_auth_token = VimDriverUtils.update_token_cache(vim, sess, tmp_auth_token, tmp_auth_state)
            content = resp.json()
            return Response(headers={'X-Subject-Token': tmp_auth_token}, data=content, status=resp.status_code)

        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, vimid="", servicetype="", regionid="", interface="", requri=""):
        logger.debug("Services--delete::data> %s" % request.data)
        logger.debug("Services--delete::vimid, servicetype, regionid, interface, requri> %s,%s,%s,%s,%s"
                     % (vimid, servicetype, regionid, interface, requri))
        try:
            # prepare request resource to vim instance
            # get token:
            tmp_auth_token = request.META.get('HTTP_X_AUTH_TOKEN', None)
            if not tmp_auth_token:
                return Response(data={'error': "No X-Auth-Token found in headers"}, status=status.HTTP_401_UNAUTHORIZED)

            # fetch the auth_state out of cache
            tmp_auth_state = cache.get(tmp_auth_token)
            if not tmp_auth_state:
                return Response(data={'error': "Expired X-Auth-Token found in headers"},
                                status=status.HTTP_401_UNAUTHORIZED)

            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid=None, auth_state=tmp_auth_state)
            req_resource = ""
            if requri != "":
                req_resource = "/" + requri

            service = {'service_type': servicetype,
                       'interface': interface,
                       'region_id': regionid}

            resp = sess.delete(req_resource, endpoint_filter=service)
            # update token cache in case the token was required during the requests
            tmp_auth_token = VimDriverUtils.update_token_cache(vim, sess, tmp_auth_token, tmp_auth_state)
            content = resp.json()
            return Response(headers={'X-Subject-Token': tmp_auth_token}, data=content, status=resp.status_code)

        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
