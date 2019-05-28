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

from common.exceptions import VimDriverNewtonException

from newton_base.util import VimDriverUtils
from common.msapi import extsys

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

    def __init__(self):
        super(Volumes, self).__init__()
        self._logger = logger

    def get(self, request, vimid="", tenantid="", volumeid=""):
        logger.info("vimid, tenantid, volumeid = %s,%s,%s" % (vimid, tenantid, volumeid))
        if request.data:
            logger.debug("With data = %s" % request.data)
            pass
        try:
            # prepare request resource to vim instance
            query = VimDriverUtils.get_query_part(request)
            content, status_code = self._get_volumes(query, vimid, tenantid, volumeid)
            logger.info("response with status = %s" % status_code)
            return Response(data=content, status=status_code)
        except VimDriverNewtonException as e:
            logger.error("response with status = %s" % e.status_code)
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_volumes(self, query="", vimid="", tenantid="", volumeid=None):

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

        self.service['region_name'] = vim['openstack_region_id'] \
            if vim.get('openstack_region_id') \
            else vim['cloud_region_id']

        logger.info("making request with URI:%s" % req_resouce)
        resp = sess.get(req_resouce, endpoint_filter=self.service)
        logger.info("request returns with status %s" % resp.status_code)
        if resp.status_code == status.HTTP_200_OK:
            logger.debug("with content:%s" % resp.json())
            pass
        content = resp.json()
        vim_dict = {
            "vimName": vim["name"],
            "vimId": vim["vimId"],
            "cloud-owner": vim["cloud_owner"],
            "cloud-region-id": vim["cloud_region_id"],
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
        logger.info("vimid, tenantid, volumeid = %s,%s,%s" % (vimid, tenantid, volumeid))
        if request.data:
            logger.debug("With data = %s" % request.data)
            pass
        try:
            #check if created already: check name
            query = "name=%s" % request.data["name"]
            content, status_code = self._get_volumes(query, vimid, tenantid)
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

            self.service['region_name'] = vim['openstack_region_id'] \
                if vim.get('openstack_region_id') \
                else vim['cloud_region_id']

            logger.info("making request with URI:%s" % req_resouce)
            logger.debug("with data:%s" % req_body)
            resp = sess.post(req_resouce, data=req_body,
                             endpoint_filter=self.service, headers={"Content-Type": "application/json",
                             "Accept": "application/json" })
            logger.info("request returns with status %s" % resp.status_code)
            resp_body = resp.json()["volume"]
            VimDriverUtils.replace_key_by_mapping(resp_body, self.keys_mapping)
            vim_dict = {
                "vimName": vim["name"],
                "vimId": vim["vimId"],
                "cloud-owner": vim["cloud_owner"],
                "cloud-region-id": vim["cloud_region_id"],
                "tenantId": tenantid,
                "returnCode": 1,
            }
            resp_body.update(vim_dict)
            return Response(data=resp_body, status=resp.status_code)
        except VimDriverNewtonException as e:
            logger.error("response with status = %s" % e.status_code)
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, vimid="", tenantid="", volumeid=""):
        logger.info("vimid, tenantid, volumeid = %s,%s,%s" % (vimid, tenantid, volumeid))
        if request.data:
            logger.debug("With data = %s" % request.data)
            pass
        try:
            # prepare request resource to vim instance
            req_resouce = "volumes"
            if volumeid:
                req_resouce += "/%s" % volumeid

            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid)

            self.service['region_name'] = vim['openstack_region_id'] \
                if vim.get('openstack_region_id') \
                else vim['cloud_region_id']

            logger.info("making request with URI:%s" % req_resouce)
            resp = sess.delete(req_resouce, endpoint_filter=self.service)
            logger.info("request returns with status %s" % resp.status_code)
            return Response(status=resp.status_code)
        except VimDriverNewtonException as e:
            logger.error("response with status = %s" % e.status_code)
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class APIv1Volumes(Volumes):

    def __init__(self):
        super(APIv1Volumes, self).__init__()
        self._logger = logger

    def get(self, request, cloud_owner="", cloud_region_id="", tenantid="", volumeid=""):
        self._logger.info("%s, %s" % (cloud_owner, cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1Volumes, self).get(request, vimid, tenantid, volumeid)

    def post(self, request, cloud_owner="", cloud_region_id="", tenantid="", volumeid=""):
        self._logger.info("%s, %s" % (cloud_owner, cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1Volumes, self).post(request, vimid, tenantid, volumeid)

    def delete(self, request, cloud_owner="", cloud_region_id="", tenantid="", volumeid=""):
        self._logger.info("%s, %s" % (cloud_owner, cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1Volumes, self).delete(request, vimid, tenantid, volumeid)
