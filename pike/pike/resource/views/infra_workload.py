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
from common.exceptions import VimDriverNewtonException
from newton_base.util import VimDriverUtils

logger = logging.getLogger(__name__)


class InfraWorkload(APIView):

    def __init__(self):
        self._logger = logger

    def post(self, request, vimid=""):
        self._logger.info("vimid: %s" % (vimid))
        self._logger.info("data: %s" % request.data)
        self._logger.debug("META: %s" % request.META)

        try :
            data = request.data
            oof_directive = data["oof_directive"]
            template_type = data["template_type"]
            template_data = data["template_data"]

            resp_template = None
            if template_type and "heat" == template_type.lower():
                # update heat parameters from oof_directive
                parameters = template_data.get("parameters", {})

                for directive in oof_directive.get("directives", []):
                    if directive["type"] == "vnfc":
                        for directive2 in directive.get("directives", []):
                            if directive2["type"] in ["flavor_directives", "sriovNICNetwork_directives"]:
                                for attr in directives2.get("attributes", []):
                                    label_name = directive2[0]["attribute_name"]
                                    label_value = directive2[0]["attribute_value"]
                                    if parameters.has_key(label_name):
                                        template_data["parameters"][label_name] = label_value
                                    else:
                                        self._logger.warn("There is no parameter exist: %s" % label_name)

                # update parameters
                template_data["parameters"] = parameters

                #reset to make sure "files" are empty
                template_data["file"] = {}

                #authenticate
                cloud_owner, regionid = extsys.decode_vim_id(vimid)
                # should go via multicloud proxy so that the selflink is updated by multicloud
                retcode, v2_token_resp_json, os_status = helper.MultiCloudIdentityHelper(
                                                 settings.MULTICLOUD_API_V1_PREFIX,
                                                 cloud_owner, regionid, "/v2.0/tokens")
                if retcode > 0 or not v2_token_resp_json:
                    logger.error("authenticate fails:%s,%s, %s" %
                                 (cloud_owner, regionid, v2_token_resp_json))
                    return

                service_type = "orchestration"
                resource_uri = "/stacks"
                self._logger.info("retrieve stack resources, URI:%s" % resource_uri)
                retcode, content, os_status = helper.MultiCloudServiceHelper(cloud_owner,
                                                         regionid, v2_token_resp_json, service_type,
                                                         resource_uri, None, "POST")
                stack1 = content.get('stack', None) if retcode == 0 and content else None
                resp_template = {
                    "template_type": template_type,
                    "workload_id": stack1["id"] if stack1 else "",
                    "template_response": content
                }
                self._logger.info("RESP with data> result:%s" % resp_template)

                return Response(data=resp_template, status=os_status)

            else:
                msg = "The template type %s is not supported" % (template_type)
                self._logger.warn(msg)
                return Response(data={"error":msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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


    def get(self, request, vimid=""):
        self._logger.info("vimid: %s" % (vimid))
        self._logger.debug("META: %s" % request.META)

        try :

            # stub response
            resp_template = {
                "template_type": "heat",
                "workload_id": "3095aefc-09fb-4bc7-b1f0-f21a304e864c",
                "workload_status": "CREATE_IN_PROCESS",
            }

            self._logger.info("RESP with data> result:%s" % resp_template)
            return Response(data=resp_template, status=status.HTTP_200_OK)
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

    def delete(self, request, vimid=""):
        self._logger.info("vimid: %s" % (vimid))
        self._logger.debug("META: %s" % request.META)

        try :

            # stub response
            self._logger.info("RESP with data> result:%s" % "")
            return Response(status=status.HTTP_204_NO_CONTENT)
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
