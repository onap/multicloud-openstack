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

from rest_framework import status

from django.conf import settings
from common.exceptions import VimDriverNewtonException
from newton_base.util import VimDriverUtils

from keystoneauth1.exceptions import HttpError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from common.msapi import extsys


logger = logging.getLogger(__name__)


class InfraWorkload(APIView):

    def __init__(self):
        self._logger = logger

    def post(self, request, vimid=""):
        self._logger.info("vimid, data: %s, %s" % (vimid, request.data))
        self._logger.debug("META: %s" % request.META)

        try :

            # stub response
            resp_template = {
                "template_type": "heat",
                "workload_id": "3095aefc-09fb-4bc7-b1f0-f21a304e864c",
                "template_response":
                {
                    "stack": {
                        "id": "3095aefc-09fb-4bc7-b1f0-f21a304e864c",
                        "links": [
                            {
                                "href": "http://192.168.123.200:8004/v1/eb1c63a4f77141548385f113a28f0f52/stacks/teststack/3095aefc-09fb-4bc7-b1f0-f21a304e864c",
                                "rel": "self"
                            }
                        ]
                    }
                }
            }

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
