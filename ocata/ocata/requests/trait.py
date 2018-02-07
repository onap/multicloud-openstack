# Copyright (c) 2018 Intel Corporation, Inc.
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
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from newton.pub.exceptions import VimDriverNewtonException
from newton.requests.views.util import VimDriverUtils

logger = logging.getLogger(__name__)

class Traits(APIView):
    service = {'service_type': 'compute',
               'interface': 'public'}

    def get(self, request, vimid="", tenantid="", traitname=""):
        logger.debug("Traits--get::> %s" % request.data)
        try:
            # prepare request resource to vim instance
            query = VimDriverUtils.get_query_part(request)
            content, status_code = self.get_traits(query, vimid,
                                                   tenantid, traitname)
            return Response(data=content, status=status_code)
        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_traits(self, query="", vimid="", tenantid="", traitname=""):
        logger.debug("Traits--get_traits::> %s,%s" % (tenantid, traitname))

        # prepare request resource to vim instance
        req_resource = "/traits"
        if traitname:
            req_resource += "/%s" % traitname
        else:
            if query:
                req_resource += "?%s" % query

        vim = VimDriverUtils.get_vim_info(vimid)
        sess = VimDriverUtils.get_session(vim, tenantid)
        resp = sess.get(req_resource, endpoint_filter=self.service)
        if resp.json() is not None:
            content = resp.json()
        else:
            content = {}
        vim_dict = {
            "vimName": vim["name"],
            "vimId": vim["vimId"],
            "tenantId": tenantid,
        }
        #content.update(vim_dict)

        return content, resp.status_code

    def put(self, request, vimid="", tenantid="", traitname=""):
        logger.debug("Traits--put::> %s" % traitname)
        sess = None
        resp = None
        resp_body = None
        try:
            # check if trait already exists: check name
            content, status_code = self.get_traits(vimid=vimid,
                                                   tenantid=tenantid,
                                                   traitname=traitname)
            existed = False if status_code == 404 else True
            if existed:
                vim_dict = {
                    "returnCode": 0,
                }
                content.update(vim_dict)
                return Response(data=content, status=status_code)

            # prepare request resource to vim instance
            req_resource = "traits"

            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid)
            req_resource = "traits/%s" % traitname
            resp = sess.put(req_resource, endpoint_filter=self.service)

            vim_dict = {
                "vimName": vim["name"],
                "vimId": vim["vimId"],
                "tenantId": tenantid,
                "returnCode": 1,
            }

            return Response(data=vim_dict, status=resp.status_code)
        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, vimid="", tenantid="", traitname=""):
        logger.debug("Traits--delete::> %s" % traitname)
        try:
            # prepare request resource to vim instance
            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid)

            req_resource = "/traits"
            if traitname:
                req_resource += "/%s" % traitname
            else:
                raise VimDriverNewtonException(message="VIM exception",
                        content="internal bug in deleting trait",
                        status_code=500)

            resp = sess.delete(req_resource, endpoint_filter=self.service)
            return Response(status=resp.status_code)
        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
