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
from six.moves import urllib
import threading
import traceback
from keystoneauth1.exceptions import HttpError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from newton.pub.exceptions import VimDriverNewtonException

from newton.requests.views.util import VimDriverUtils

logger = logging.getLogger(__name__)

running_threads = {}
running_thread_lock = threading.Lock()

class imageThread (threading.Thread):
    service = {'service_type': 'image',
               'interface': 'public'}
    def __init__(self, vimid, tenantid, imageid, imagefd):
        threading.Thread.__init__(self)
        self.vimid = vimid
        self.tenantid = tenantid
        self.imageid = imageid
        self.imagefd = imagefd

    def run(self):
        logger.debug("start imagethread %s, %s, %s" % (self.vimid, self.tenantid, self.imageid))
        self.transfer_image(self.vimid, self.tenantid, self.imageid, self.imagefd)
        logger.debug("stop imagethread %s, %s, %s" % (self.vimid, self.tenantid, self.imageid))
        running_thread_lock.acquire()
        running_threads.pop(self.imageid)
        running_thread_lock.release()

    def transfer_image(self, vimid, tenantid, imageid, imagefd):
        logger.debug("Images--transfer_image::> %s" % (imageid))
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
        pass

class Images(APIView):
    service = {'service_type': 'image',
               'interface': 'public'}
    keys_mapping = [
        ("project_id", "tenantId"),
        ("disk_format", "imageType"),
        ("container_format", "containerFormat")
    ]

    def get(self, request, vimid="", tenantid="", imageid=""):
        logger.debug("Images--get::> %s" % request.data)
        try:
            # prepare request resource to vim instance
            query = VimDriverUtils.get_query_part(request)
            content, status_code = self.get_images(query, vimid, tenantid, imageid)
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

    def get_images(self, query="", vimid="", tenantid="", imageid=""):
        logger.debug("Images--get_images::> %s" % imageid)

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
        logger.debug("Images--post::> %s" % request.data)
        try:
            #check if created already: check name
            query = "name=%s" % request.data["name"]
            content, status_code = self.get_images(query, vimid, tenantid)
            existed = False
            if status_code == 200:
                for image in content["images"]:
                    if image["name"] == request.data["name"]:
                        existed = True
                        break
                    pass
                if existed == True:
                    vim_dict = {
                        "returnCode": 0,
                    }
                    image.update(vim_dict)
                    return Response(data=image, status=status_code)

            imageurl = request.data.pop("imagePath", None)
            imagefd = None
            if not imageurl:
                return Response(data={'error': 'imagePath is not specified'}, status=500)

            #valid image url
            imagefd = urllib2.urlopen(imageurl)
            if not imagefd:
                logger.debug("image is not available at %s" % imageurl)
                return Response(data={'error': 'cannot access to specified imagePath'}, status=500)

                # prepare request resource to vim instance
            req_resouce = "v2/images"

            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid)
            image = request.data
            VimDriverUtils.replace_key_by_mapping(image,
                                                  self.keys_mapping, True)
            #req_body = json.JSONEncoder().encode({"image": image})
            req_body = json.JSONEncoder().encode(image)
            resp = sess.post(req_resouce, data=req_body,
                             endpoint_filter=self.service)
            #resp_body = resp.json()["image"]
            resp_body = resp.json()
            VimDriverUtils.replace_key_by_mapping(resp_body, self.keys_mapping)
            vim_dict = {
                "vimName": vim["name"],
                "vimId": vim["vimId"],
                "tenantId": tenantid,
                "returnCode": 1,
            }
            resp_body.update(vim_dict)

            #launch a thread to download image and upload to VIM
            if resp.status_code == 201:
                imageid = resp_body["id"]
                logger.debug("launch thread to upload image: %s" % imageid)
                tmp_thread = imageThread(vimid, tenantid,imageid,imagefd)
                running_thread_lock.acquire()
                running_threads[imageid] = tmp_thread
                running_thread_lock.release()
                tmp_thread.start()
            else:
                logger.debug("resp.status_code: %s" % resp.status_code)
                pass

            return Response(data=resp_body, status=resp.status_code)
        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except urllib2.URLError as e:
            return Response(data={'error': 'image is not accessible:%s' % str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except HttpError as e:
            logger.error("HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        pass

    def delete(self, request, vimid="", tenantid="", imageid=""):
        logger.debug("Images--delete::> %s" % request.data)
        try:
            # prepare request resource to vim instance
            req_resouce = "v2/images"
            if imageid:
                req_resouce += "/%s" % imageid

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
        pass
