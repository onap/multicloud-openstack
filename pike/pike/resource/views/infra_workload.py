# Copyright (c) 2018 Intel Corporation.
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

import json
import logging
import traceback

from django.conf import settings
from keystoneauth1.exceptions import HttpError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.msapi import extsys
from common.msapi.helper import Helper as helper
from common.utils import restcall
from common.exceptions import VimDriverNewtonException
from newton_base.util import VimDriverUtils

logger = logging.getLogger(__name__)


class InfraWorkload(APIView):

    def __init__(self):
        self._logger = logger

    def post(self, request, vimid=""):
        self._logger.info("vimid, data: %s, %s" % (vimid, request.data))
        self._logger.debug("META: %s" % request.META)

        try :
            vim = VimDriverUtils.get_vim_info(vimid)
            cloud_owner, regionid = extsys.decode_vim_id(vimid)

            data = request.data
            oof_directive = data["oof_directive"]
            template_type = data["template_type"]
            template_data = data["template_data"]

            resp_template = None
            if "heat" == template_type:
                tenant_name = None
                interface = 'public'
                service = {'service_type': 'orchestration',
                           'interface': interface,
                           'region_id': vim['openstack_region_id']
                               if vim.get('openstack_region_id')
                                else vim['cloud_region_id']}

                if template_data.has_key("parameters"):
                    paramters = template_data["parameters"]
                else:
                    self._logger.error("we can't find parameters in heat template")
                    return Response(data=None, status=HTTP_400_BADREQUEST)

                for directive in template_data["directives"]:
                    if directive["type"] == "vnfc":
                        for directive2 in directive["directives"]:
                            if directive2["type"] == flavor_directive:
                                flavor_label = directive2[0]["attribute_name"]
                                flavor_value = directive2[0]["attribute_value"]
                                if parameters.has_key(flavor_label):
                                    template_data["parameters"][flavor_label] = flavor_value
                                else:
                                    self._logger.warn("we can't find the flavor_label: %s" % 
                                                        flavor_label)

                req_body = template_data
                sess = VimDriverUtils.get_session(vim, tenant_name)
                resp = sess.post(req_resource,
                                 data = req_body,
                                 endpoint_filter = service)

                resp_template = {
                    "template_type": template_type,
                    "workload_id": resp["stack"]["id"],
                    "template_response": resp
                }

            elif "tosca" == template_type:
                #TODO
                self._logger.info("TBD")
            else:
                self._logger.warn("This template type is not supported")


            self._logger.info("RESP with data> result:%s" % resp_template)
            return Response(data=resp_template, status=status.HTTP_201_CREATED)
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


    def get(self, request, vimid="", requri=""):
        self._logger.info("vimid, requri: %s, %s" % (vimid, requri))
        self._logger.debug("META: %s" % request.META)

        try :
            # we just support heat template
            workload_id = requri
            tenant_name = None
            vim = VimDriverUtils.get_vim_info(vimid)
            cloud_owner, regionid = extsys.decode_vim_id(vimid)
            v2_token_resp_json = helper.MultiCloudIdentityHelper(settings.MULTICLOUD_API_V1_PREFIX,
                                                             cloud_owner, regionid, "/v2.0/tokens")
            if not v2_token_resp_json:
                logger.error("authenticate fails:%s,%s" % (cloud_owner, regionid))
                return
            tenant_id = v2_token_resp_json["access"]["token"]["tenant"]["id"]
            req_source = "/v1/%s/stacks" % (tenant_id)
 
            interface = 'public'
            service = {'service_type': 'orchestration',
                       'interface': interface,
                       'region_id': vim['openstack_region_id']
                             if vim.get('openstack_region_id')
                             else vim['cloud_region_id']}

            req_body = template_data
            sess = VimDriverUtils.get_session(vim, tenant_name)
            resp = sess.get(req_resource,
                            data = req_body,
                            endpoint_filter = service)

            stack_info = resp.json()
            stacks = stack_info["stacks"]
            for stack in stacks:
                if workload_id == stack["id"]:
                    break
            stack_name = stack["stack_name"]
            stack_status = stack["stack_status"]
            req_source = "/v1/%s/stacks/%s/%s" % (tenant_id, stack_name, workload_id)
            resp_template = {
                "template_type": template_type,
                "workload_id": workload_id,
                "workload_status": stack_status
            }

            resp_status = status.HTTP_200_OK
            self._logger.info("RESP with data> result:%s" % resp_template)
            return Response(data=resp_template, status=resp_status)
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

    def delete(self, request, vimid="", requri=""):
        self._logger.info("vimid, requri: %s" % (vimid, requri))
        self._logger.debug("META: %s" % request.META)

        try :
            # we just support heat template
            workload_id = requri
            tenant_name = None
            vim = VimDriverUtils.get_vim_info(vimid)
            cloud_owner, regionid = extsys.decode_vim_id(vimid)
            v2_token_resp_json = helper.MultiCloudIdentityHelper(settings.MULTICLOUD_API_V1_PREFIX,
                                                             cloud_owner, regionid, "/v2.0/tokens")
            if not v2_token_resp_json:
                logger.error("authenticate fails:%s,%s" % (cloud_owner, regionid))
                return
            tenant_id = v2_token_resp_json["access"]["token"]["tenant"]["id"]
            interface = 'public'
            service = {'service_type': 'orchestration',
                       'interface': interface,
                       'region_id': vim['openstack_region_id']
                           if vim.get('openstack_region_id')
                           else vim['cloud_region_id']}

            req_body = template_data
            url_get = "/v1/%s/stacks" % (tenant_id)
            sess = VimDriverUtils.get_session(vim, tenant_name)
            get_resp = sess.get(url_get,
                            data = req_body,
                            endpoint_filter = service)
            stack_info = get_resp.json()
            stacks = stack_info["stacks"]
            stack_name = ""
            for stack in stacks:
                if workload_id == stack["id"]:
                    stack_name = stack["stack_name"]
                    break

            req_source = "/v1/%s/stacks/%s/%s" % (tenant_id, stack_name, workload_id)
            resp = sess.delete(req_resource,
                               endpoint_filter = service)

            resp_status = status.HTTP_204_NO_CONTENT
            self._logger.info("RESP with data> result:%s" % "")
            return Response(status=resp_status)
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


class APIv1InfraWorkload(InfraWorkload):

    def __init__(self):
        super(APIv1InfraWorkload, self).__init__()
        # self._logger = logger

    def post(self, request, cloud_owner="", cloud_region_id=""):
        #self._logger.info("cloud owner, cloud region id, data: %s,%s, %s" % (cloud_owner, cloud_region_id, request.data))
        #self._logger.debug("META: %s" % request.META)

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1InfraWorkload, self).post(request, vimid)

    def get(self, request, cloud_owner="", cloud_region_id=""):
        #self._logger.info("cloud owner, cloud region id, data: %s,%s, %s" % (cloud_owner, cloud_region_id, request.data))
        #self._logger.debug("META: %s" % request.META)

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1InfraWorkload, self).get(request, vimid)

    def delete(self, request, cloud_owner="", cloud_region_id=""):
        #self._logger.info("cloud owner, cloud region id, data: %s,%s, %s" % (cloud_owner, cloud_region_id, request.data))
        #self._logger.debug("META: %s" % request.META)

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1InfraWorkload, self).delete(request, vimid)
