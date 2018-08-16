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

from keystoneauth1.exceptions import HttpError
import re
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from newton_base.proxy.services import Services

from newton_base.proxy.proxy_utils import ProxyUtils
from common.exceptions import VimDriverNewtonException
from common.msapi import extsys
from newton_base.util import VimDriverUtils


logger = logging.getLogger(__name__)

# DEBUG=True

class DnsaasDelegate(Services):
    '''
    DNSaaS delegate service
    '''

    def __init__(self):
        self._logger = logger


    def _do_action(self, action, request, vim_id, servicetype, requri):
        tmp_auth_token = self._get_token(request)
        try:
            # fetch the auth_state out of cache
            auth_state_str, metadata_catalog_str = VimDriverUtils.get_token_cache(tmp_auth_token)

            if not auth_state_str:
                #invalid token
                msg = {
                    'error': "request token %s is not valid" % (tmp_auth_token)
                }
                self._logger.warn("RESP with status, msg> %s , %s"
                                  % (status.HTTP_404_NOT_FOUND, msg))

                return Response(data=msg,
                                status=status.HTTP_404_NOT_FOUND)

            # get project name from auth_state
            auth_state = json.loads(auth_state_str)
            if not auth_state:
                # invalid token
                msg = {
                    'error': "request token %s is broken" % (tmp_auth_token)
                }
                self._logger.warn("RESP with status, msg> %s , %s"
                                  % (status.HTTP_404_NOT_FOUND, msg))
                return Response(data=msg,
                                status=status.HTTP_404_NOT_FOUND)

            tenant_name = auth_state['body']['token']['project']['name']
            #tenant_id = auth_state['body']['token']['project']['id']

            #find out the delegated DNSaaS provider
            viminfo = VimDriverUtils.get_vim_info(vim_id)
            if not viminfo:
                msg = {
                    'error': "vimid %s is not found" % (vim_id)
                }
                self._logger.warn("RESP with status, msg> %s , %s"
                                  % (status.HTTP_404_NOT_FOUND, msg))
                return Response(data=msg,
                                status=status.HTTP_404_NOT_FOUND)

            cloud_dns_delegate_info = None
            cloud_extra_info_str = viminfo.get('cloud_extra_info')
            if cloud_extra_info_str:
                cloud_extra_info = json.loads(cloud_extra_info_str)
                cloud_dns_delegate_info = cloud_extra_info.get("dns-delegate")

            if not cloud_dns_delegate_info \
                    or not cloud_dns_delegate_info.get("cloud-owner") \
                    or not cloud_dns_delegate_info.get("cloud-region-id"):
                msg = {
                    'error': "dns-delegate for vimid %s is not configured"
                             % (vim_id)
                }
                self._logger.warn("RESP with status, msg> %s , %s"
                                  % (status.HTTP_404_NOT_FOUND, msg))

                return Response(data=msg,
                                status=status.HTTP_404_NOT_FOUND)

            vimid_delegate = cloud_dns_delegate_info.get("cloud-owner") \
                             + "_" \
                             + cloud_dns_delegate_info.get("cloud-region-id")


            #now forward request to delegated DNS service endpoint
            vim = VimDriverUtils.get_vim_info(vimid_delegate)
            if not vim:
                msg = {
                    'error': "delegated vimid %s is not found" % (vimid_delegate)
                }
                self._logger.warn("RESP with status, msg> %s , %s"
                                  % (status.HTTP_404_NOT_FOUND, msg))
                return Response(data=msg,
                                status=status.HTTP_404_NOT_FOUND)

            sess = VimDriverUtils.get_session(vim, tenant_name=tenant_name)

            cloud_owner, regionid = extsys.decode_vim_id(vimid_delegate)
            interface = 'public'
            service = {
                'service_type': servicetype,
                'interface': interface,
                'region_id': vim['openstack_region_id']
                           if vim.get('openstack_region_id')
                           else vim['cloud_region_id']
            }


            req_resource = requri
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

            self._logger.info("service " + action + " response status> %s" % (resp.status_code))

            content = resp.json() if resp.content else None
            self._logger.debug("service " + action + " response content> %s" % (content))

            self._logger.info("RESP with status> %s" % resp.status_code)
            if (action == "delete"):
                return Response(headers={'X-Subject-Token': tmp_auth_token}, status=resp.status_code)
            else:
                #content = ProxyUtils.update_dnsaas_project_id(content, tenant_id)
                return Response(headers={'X-Subject-Token': tmp_auth_token}, data=content, status=resp.status_code)

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

    def get(self, request, vimid="", servicetype="dns-delegate", requri=""):
        self._logger.info("vimid, servicetype, requri> %s,%s,%s"
                     % (vimid, servicetype, requri))
        self._logger.debug("META,data> %s , %s" % (request.META, request.data))

        return self._do_action("get", request, vimid, "dns", requri)

    def head(self, request, vimid="", servicetype="dns-delegate", requri=""):
        self._logger.info("vimid, servicetype, requri> %s,%s,%s"
                     % (vimid, servicetype, requri))
        self._logger.debug("META,data> %s , %s" % (request.META, request.data))

        return self._do_action("head", request, vimid, "dns", requri)

    def post(self, request, vimid="", servicetype="dns-delegate", requri=""):
        self._logger.info("vimid, servicetype, requri> %s,%s,%s"
                     % (vimid, servicetype, requri))
        self._logger.debug("META,data> %s , %s" % (request.META, request.data))

        return self._do_action("post", request, vimid, "dns", requri)

    def put(self, request, vimid="", servicetype="dns-delegate", requri=""):
        self._logger.info("vimid, servicetype, requri> %s,%s,%s"
                     % (vimid, servicetype, requri))
        self._logger.debug("META,data> %s , %s" % (request.META, request.data))

        return self._do_action("put", request, vimid, "dns", requri)

    def patch(self, request, vimid="", servicetype="dns-delegate", requri=""):
        self._logger.info("vimid, servicetype, requri> %s,%s,%s"
                     % (vimid, servicetype, requri))
        self._logger.debug("META,data> %s , %s" % (request.META, request.data))

        return self._do_action("patch", request, vimid, "dns", requri)

    def delete(self, request, vimid="", servicetype="dns-delegate", requri=""):
        self._logger.info("vimid, servicetype, requri> %s,%s,%s"
                     % (vimid, servicetype, requri))
        self._logger.debug("META,data> %s , %s" % (request.META, request.data))

        return self._do_action("delete", request, vimid, "dns", requri)



class APIv1DnsaasDelegate(Services):
    '''
    DNSaaS delegate service API V1
    '''

    def __init__(self):
        self._logger = logger

    def get(self, request, cloud_owner="", cloud_region_id="", servicetype="dns-delegate", requri=""):
        self._logger.info("cloud_owner,cloud_region_id: %s,%s" % (cloud_owner,cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1DnsaasDelegate,self).get(request, vimid, servicetype, requri)

    def head(self, request, cloud_owner="", cloud_region_id="", servicetype="dns-delegate", requri=""):
        self._logger.info("cloud_owner,cloud_region_id: %s,%s" % (cloud_owner,cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1DnsaasDelegate,self).head(request, vimid, servicetype, requri)

    def post(self, request, cloud_owner="", cloud_region_id="", servicetype="dns-delegate", requri=""):
        self._logger.info("cloud_owner,cloud_region_id: %s,%s" % (cloud_owner,cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1DnsaasDelegate,self).post(request, vimid, servicetype, requri)

    def put(self, request, cloud_owner="", cloud_region_id="", servicetype="dns-delegate", requri=""):
        self._logger.info("cloud_owner,cloud_region_id: %s,%s" % (cloud_owner,cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1DnsaasDelegate,self).put(request, vimid, servicetype, requri)

    def patch(self, request, cloud_owner="", cloud_region_id="", servicetype="dns-delegate", requri=""):
        self._logger.info("cloud_owner,cloud_region_id: %s,%s" % (cloud_owner,cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1DnsaasDelegate,self).patch(request, vimid, servicetype, requri)

    def delete(self, request, cloud_owner="", cloud_region_id="", servicetype="dns-delegate", requri=""):
        self._logger.info("cloud_owner,cloud_region_id: %s,%s" % (cloud_owner,cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1DnsaasDelegate,self).delete(request, vimid, servicetype, requri)
