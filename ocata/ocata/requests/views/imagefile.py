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
import tempfile
import os

import traceback
from keystoneauth1.exceptions import HttpError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import VimDriverNewtonException

from newton_base.util import VimDriverUtils
from newton_base.openoapi.image import Images

logger = logging.getLogger(__name__)

class ImageFile(APIView):
    service = {'service_type': 'image',
               'interface': 'public'}
    keys_mapping = [
        ("project_id", "tenantId"),
        ("disk_format", "imageType"),
        ("container_format", "containerFormat")
    ]

    def get(self, request, vimid="", tenantid="", imageid=""):
        logger.info("vimid, tenantid, imageid > %s,%s,%s" % (vimid, tenantid, imageid))
        logger.debug("META, data> %s" % (request.META, request.data))

        if not imageid or imageid == "":
            msg = {
                'error': "Operation image/file list is not available"
            }

            self._logger.warn("RESP with status, msg> %s , %s"
                                  %(status, status.HTTP_404_NOT_FOUND))

            return Response(data=msg,
                            status=status.HTTP_404_NOT_FOUND)

        try:
            # download image
            status_code = status.HTTP_200_OK

            return Response(data={'error':'to be implemented'}, status=status_code)
        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_images(self, query="", vimid="", tenantid="", imageid=""):

        # prepare request resource to vim instance
        req_resouce = "v2/images"
        if imageid:
            req_resouce += "/%s" % imageid
        elif query:
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

        if not imageid:
            # convert the key naming in images
            for image in content["images"]:
                VimDriverUtils.replace_key_by_mapping(image,
                                                      self.keys_mapping)
        else:
            # convert the key naming in the image specified by id
            #image = content.pop("image", None)
            VimDriverUtils.replace_key_by_mapping(content,
                                                  self.keys_mapping)
            #content.update(image)

        return content, resp.status_code

    def post(self, request, vimid="", tenantid="", imageid=""):
        logger.info("vimid, tenantid, imageid > %s,%s,%s" % (vimid, tenantid, imageid))
        logger.debug("META, data> %s" % (request.META, request.data))


        if imageid and imageid != "":
            msg = {
                'error': "Operation image/file create with image id is not available"
            }

            self._logger.warn("RESP with status, msg> %s , %s"
                                  %(status, status.HTTP_404_NOT_FOUND))

            return Response(data=msg,
                            status=status.HTTP_404_NOT_FOUND)

        try:
            # get file name
            image_file = request.FILES['file']

            # check if created already: check name
            query = "name=%s" % image_file.name
            content, status_code = Images.get_images(query, vimid, tenantid)
            existed = False
            if status_code == 200:
                for image in content["images"]:
                    if image["name"] == image_file.name:
                        existed = True
                        break
                if existed == True:
                    vim_dict = {
                        "returnCode": 0,
                    }
                    return Response(data=image, status=status_code)

            # not exist, download to temp file
            file_name = image_file.name[:image_file.name.rfind('.')]
            f = tempfile.NamedTemporaryFile(prefix="django_",
                                            suffix=file_name,
                                            delete=False)
            for chunk in image_file.chunks():
                f.write(chunk)

            #upload to openstack
            image_type = image_file.name[image_file.name.find('.') + 1:]

            # prepare request resource to vim instance
            req_resouce = "v2/images"

            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid)
            image = {}
            #req_body = json.JSONEncoder().encode({"image": image})
            req_body = json.JSONEncoder().encode(image)
            resp = sess.post(req_resouce, data=req_body,
                             endpoint_filter=self.service)
            #resp_body = resp.json()["image"]
            resp_body = resp.json()

            #launch a thread to download image and upload to VIM
            if resp.status_code == 201:
                imageid = resp_body["id"]
                logger.info("upload image: %s" % imageid)
                self.transfer_image(vimid, tenantid, imageid, f)
                logger.info("request '%s' success" % (req_resouce))
            else:
                logger.info("request '%s' failed with status: %s" % (req_resouce, resp.status_code))

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

        finally:
            f.close()
            os.remove(f.name)

    def transfer_image(self, vimid, tenantid, imageid, imagefd):
        logger.debug("vimid, tenantid, imageid > %s,%s,%s" % (vimid, tenantid, imageid))

        try:
            # prepare request resource to vim instance
            req_resouce = "v2/images/%s/file" % imageid

            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid)

            #open imageurl
            resp = sess.put(req_resouce, endpoint_filter=self.service, data=imagefd.read(),
                    headers={"Content-Type": "application/octet-stream",
                             "Accept": ""})

            logger.debug("response status code of transfer_image %s" % resp.status_code)
            return None
        except HttpError as e:
            logger.error("transfer_image, HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return None
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error("Failed to transfer_image:%s" % str(e))
            return None
