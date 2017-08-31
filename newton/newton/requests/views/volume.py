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
from keystoneauth1.exceptions import HttpError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from newton.pub.exceptions import VimDriverNewtonException

from util import VimDriverUtils

logger = logging.getLogger(__name__)


class Volumes(APIView):
    service = {'service_type': 'volumev2',
               'interface': 'public'}
    keys_mapping = [
        ("project_id", "tenantId"),
        ("created_at", "createTime"),
        ("size", "volumeSize"),
        ("volume_type", "volumeType"),
        ("imageRef", "imageId"),
        ("availability_zone", "availabilityZone"),
        ("server_id", "serverId"),
        ("attachment_id", "attachmentId"),
    ]

    def get(self, request, vimid="", tenantid="", volumeid=""):
        logger.debug("Volumes--get::> %s" % request.data)
        try:
            # prepare request resource to vim instance
            query = VimDriverUtils.get_query_part(request)
            content, status_code = self.get_volumes(query, vimid, tenantid, volumeid)
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

    def get_volumes(self, query="", vimid="", tenantid="", volumeid=None):
        logger.debug("Volumes--get_volumes::> %s,%s" % (tenantid, volumeid))

        # prepare request resource to vim instance
        req_resouce = "volumes"
        if volumeid:
            req_resouce += "/%s" % volumeid
        else:
            req_resouce += "/detail"
            if query:
                req_resouce += "?%s" % query

        vim = VimDriverUtils.get_vim_info(vimid)
        sess = VimDriverUtils.get_session(vim, tenantid)
        resp = sess.get(req_resouce, endpoint_filter=self.service)
        content = resp.json()
        vim_dict = {
            "vimName": vim["name"],
            "vimId": vim["vimId"],
            "tenantId": tenantid,
        }
        content.update(vim_dict)

        if not volumeid:
            # convert the key naming in volumes
            for volume in content["volumes"]:
                VimDriverUtils.replace_key_by_mapping(volume,
                                                      self.keys_mapping)
        else:
            # convert the key naming in the volume specified by id
            volume = content.pop("volume", None)
            VimDriverUtils.replace_key_by_mapping(volume,
                                                  self.keys_mapping)
            content.update(volume)

        return content, resp.status_code

    def post(self, request, vimid="", tenantid="", volumeid=""):
        logger.debug("Volumes--post::> %s" % request.data)
        try:
            #check if created already: check name
            query = "name=%s" % request.data["name"]
            content, status_code = self.get_volumes(query, vimid, tenantid)
            existed = False
            if status_code == 200:
                for volume in content["volumes"]:
                    if volume["name"] == request.data["name"]:
                        existed = True
                        break
                if existed == True:
                    vim_dict = {
                        "returnCode": 0,
                    }
                    volume.update(vim_dict)
                    return Response(data=volume, status=status_code)

            # prepare request resource to vim instance
            req_resouce = "volumes"

            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid)
            volume = request.data
            VimDriverUtils.replace_key_by_mapping(volume,
                                                  self.keys_mapping, True)
            req_body = json.JSONEncoder().encode({"volume": volume})
            resp = sess.post(req_resouce, data=req_body,
                             endpoint_filter=self.service, headers={"Content-Type": "application/json",
                             "Accept": "application/json" })
            resp_body = resp.json()["volume"]
            VimDriverUtils.replace_key_by_mapping(resp_body, self.keys_mapping)
            vim_dict = {
                "vimName": vim["name"],
                "vimId": vim["vimId"],
                "tenantId": tenantid,
                "returnCode": 1,
            }
            resp_body.update(vim_dict)
            return Response(data=resp_body, status=resp.status_code)
        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, vimid="", tenantid="", volumeid=""):
        logger.debug("Volumes--delete::> %s" % request.data)
        try:
            # prepare request resource to vim instance
            req_resouce = "volumes"
            if volumeid:
                req_resouce += "/%s" % volumeid

            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid)
            resp = sess.delete(req_resouce, endpoint_filter=self.service)
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
