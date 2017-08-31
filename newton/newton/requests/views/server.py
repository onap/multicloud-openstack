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
import urllib2
import threading
import traceback
from keystoneauth1.exceptions import HttpError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from newton.pub.exceptions import VimDriverNewtonException

from util import VimDriverUtils

logger = logging.getLogger(__name__)


running_threads = {}
running_thread_lock = threading.Lock()

#assume volume is attached on server creation
class serverThread (threading.Thread):
    service = {'service_type': 'compute',
               'interface': 'public'}
    def __init__(self, vimid, tenantid, serverid, is_attach, *volumeids):
        threading.Thread.__init__(self)
        self.vimid = vimid
        self.tenantid = tenantid
        self.serverid = serverid
        self.volumeids = volumeids
        self.is_attach = is_attach

    def run(self):
        logger.debug("start server thread %s, %s, %s" % (self.vimid, self.tenantid, self.serverid))
        if (self.is_attach):
            self.attach_volume(self.vimid, self.tenantid, self.serverid, *self.volumeids)
        else:
            elf.detach_volume(self.vimid, self.tenantid, self.serverid, *self.volumeids)
        logger.debug("stop server thread %s, %s, %s" % (self.vimid, self.tenantid, self.serverid))
        running_thread_lock.acquire()
        running_threads.pop(self.serverid)
        running_thread_lock.release()

    def attach_volume(self, vimid, tenantid, serverid, *volumeids):
        logger.debug("Server--attach_volume::> %s, %s" % (serverid, volumeids))
        try:
            # prepare request resource to vim instance
            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid)

            #check if server is ready to attach
            logger.debug("Servers--attach_volume, wait for server to be ACTIVE::>%s" % serverid)
            req_resouce = "servers/%s" % serverid
            while True:
                resp = sess.get(req_resouce, endpoint_filter=self.service)
                content = resp.json()
                if content and content["server"] and content["server"]["status"] == "ACTIVE":
                    break;

            for volumeid in volumeids:
                req_resouce = "servers/%s/os-volume_attachments" % serverid
                req_data = {"volumeAttachment": {
                    "volumeId": volumeid
                }}
                logger.debug("Servers--attach_volume::>%s, %s" % (req_resouce, req_data))
                req_body = json.JSONEncoder().encode(req_data)
                resp = sess.post(req_resouce, data=req_body,
                                 endpoint_filter=self.service,
                                 headers={"Content-Type": "application/json",
                                          "Accept": "application/json"})
                logger.debug("Servers--attach_volume resp::>%s" % resp.json())

            return None
        except HttpError as e:
            logger.error("attach_volume, HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return None
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.debug("Failed to attach_volume:%s" % str(e))
            return None


    def detach_volume(self, vimid, tenantid, serverid, *volumeids):
        logger.debug("Server--detach_volume::> %s, %s" % (serverid, volumeids))
        try:
            # prepare request resource to vim instance
            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid)

            #wait server to be ready to detach volume

            # assume attachment id is the same as volume id
            for volumeid in volumeids:
                req_resouce = "servers/%s/os-volume_attachments/%s" % (serverid, volumeid)

                logger.debug("Servers--dettachVolume::>%s" % (req_resouce))
                resp = sess.delete(req_resouce,
                                   endpoint_filter=self.service,
                                   headers={"Content-Type": "application/json",
                                            "Accept": "application/json"})

                logger.debug("Servers--dettachVolume resp::>%s" % resp.json())

            return None
        except HttpError as e:
            logger.error("detach_volume, HttpError: status:%s, response:%s" % (e.http_status, e.response.json()))
            return None
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.debug("Failed to detach_volume:%s" % str(e))
            return None

class Servers(APIView):
    service = {'service_type': 'compute',
               'interface': 'public'}
    keys_mapping = [
        ("tenant_id", "tenantId"),
        ("flavorRef", "flavorId"),
        ("user_data", "userdata"),
        ("security_groups", "securityGroups"),
        ("availability_zone ", "availabilityZone"),
        ("os-extended-volumes:volumes_attached", "volumeArray"),
    ]

    def attachVolume(self, vimid, tenantid, serverId, *volumeIds):
        #has to be async mode to wait server is ready to attach volume
        logger.debug("launch thread to attach volume: %s" % serverId)
        tmp_thread = serverThread(vimid, tenantid, serverId, True, *volumeIds)
        running_thread_lock.acquire()
        running_threads[serverId] = tmp_thread
        running_thread_lock.release()
        tmp_thread.start()

    def dettachVolume(self, vimid, tenantid, serverId, *volumeIds):
        # assume attachment id is the same as volume id
        vim = VimDriverUtils.get_vim_info(vimid)
        sess = VimDriverUtils.get_session(vim, tenantid)

        for volumeid in volumeIds:
            req_resouce = "servers/%s/os-volume_attachments/%s" % (serverId, volumeid)
            logger.debug("Servers--dettachVolume::>%s" % (req_resouce))
            resp = sess.delete(req_resouce,
                               endpoint_filter=self.service,
                               headers={"Content-Type": "application/json",
                                        "Accept": "application/json"})
            logger.debug("Servers--dettachVolume resp status::>%s" % resp.status_code)


    def convertMetadata(self, metadata, mata_data, reverse=False):
        if reverse == False:
            # from extraSpecs to extra_specs
            for spec in metadata:
                mata_data[spec['keyName']] = spec['value']
        else:
            for k, v in mata_data.items():
                spec = {}
                spec['keyName'] = k
                spec['value'] = v
                metadata.append(spec)


    def convert_resp(self, server):
        #convert volumeArray
        volumeArray = server.pop("volumeArray", None)
        tmpVolumeArray = []
        if volumeArray and len(volumeArray) > 0:
            for vol in volumeArray:
                tmpVolumeArray.append({"volumeId": vol["id"]})
        server["volumeArray"] = tmpVolumeArray if len(tmpVolumeArray) > 0 else None

        #convert flavor
        flavor = server.pop("flavor", None)
        server["flavorId"] = flavor["id"] if flavor else None

        #convert nicArray

        #convert boot
        imageObj = server.pop("image", None)
        imageId = imageObj.pop("id", None) if imageObj else None
        if imageId:
            server["boot"] = {"type":2, "imageId": imageId}
        else:
            server["boot"] = {"type":1, "volumeId":tmpVolumeArray.pop(0)["volumeId"] if len(tmpVolumeArray) > 0 else None}

        #convert OS-EXT-AZ:availability_zone
        server["availabilityZone"] = server.pop("OS-EXT-AZ:availability_zone", None)

    def get(self, request, vimid="", tenantid="", serverid=""):
        logger.debug("Servers--get::> %s" % request.data)
        try:
            # prepare request resource to vim instance
            query = VimDriverUtils.get_query_part(request)
            content, status_code = self.get_servers(query, vimid, tenantid, serverid)
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

    def get_ports(self, vimid="", tenantid="", serverid=None):
        # query attached ports
        vim = VimDriverUtils.get_vim_info(vimid)
        sess = VimDriverUtils.get_session(vim, tenantid)
        req_resouce = "servers/%s/os-interface" % serverid
        resp = sess.get(req_resouce, endpoint_filter=self.service)
        ports = resp.json()
        if ports and ports["interfaceAttachments"] and len(ports["interfaceAttachments"]) > 0:
            return [{"portId":port["port_id"]} for port in ports["interfaceAttachments"]]
        else:
            return None

    def get_servers(self, query="", vimid="", tenantid="", serverid=None):
        logger.debug("Servers--get_servers::> %s,%s" % (tenantid, serverid))

        # prepare request resource to vim instance
        req_resouce = "servers"
        if serverid:
            req_resouce += "/%s" % serverid
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

        if not serverid:
            # convert the key naming in servers
            for server in content["servers"]:
                metadata = server.pop("metadata", None)
                if metadata:
                    meta_data = []
                    self.convertMetadata(metadata, meta_data, True)
                    server["metadata"] = meta_data
                VimDriverUtils.replace_key_by_mapping(server,
                                                      self.keys_mapping)
                self.convert_resp(server)
                server["nicArray"] = self.get_ports(vimid, tenantid, server["id"])

        else:
            # convert the key naming in the server specified by id
            server = content.pop("server", None)
            metadata = server.pop("metadata", None)
            if metadata:
                meta_data = []
                self.convertMetadata(metadata, meta_data, True)
                server["metadata"] = meta_data
            VimDriverUtils.replace_key_by_mapping(server,
                                                  self.keys_mapping)
            self.convert_resp(server)
            server["nicArray"] = self.get_ports(vimid, tenantid, serverid)
            content.update(server)

        return content, resp.status_code

    def post(self, request, vimid="", tenantid="", serverid=""):
        logger.debug("Servers--post::> %s" % request.data)
        try:
            # check if created already: check name
            servername = request.data["name"]
            query = "name=%s" % servername
            content, status_code = self.get_servers(query, vimid, tenantid)
            existed = False
            if status_code == 200:
                for server in content["servers"]:
                    if server["name"] == request.data["name"]:
                        existed = True
                        break
                if existed == True and server:
                    vim_dict = {
                        "returnCode": 0,
                    }
                    server.update(vim_dict)
                    return Response(data=server, status=status_code)

            # prepare request resource to vim instance
            req_resouce = "servers"

            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid)
            server = request.data

            # convert parameters
            boot = server.pop("boot", None)
            if not boot:
                return Response(data={'error': "missing boot paramters"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            if boot["type"] == 1:
                # boot from volume
                server["block_device_mapping_v2"] = [{"uuid": boot["volumeId"],
                                                      "source_type": "volume",
                                                      "destination_type": "volume",
                                                      "delete_on_termination": "false",
                                                      "boot_index": "0"}]
            else:
                # boot from image
                server["imageRef"] = boot["imageId"]

            nicarray = server.pop("nicArray", None)
            if not nicarray:
                return Response(data={'error': "missing nicArray paramters"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                networks = []
                for nic in nicarray:
                    networks.append({"port": nic["portId"]})
                if len(networks) > 0:
                    server["networks"] = networks

            meta_data = server.pop("metadata", None)
            if meta_data:
                metadata = {}
                self.convertMetadata(metadata, meta_data, False)
                server["metadata"] = metadata

            contextarray = server.pop("contextArray", None)
            if contextarray:
                # now set "contextArray" array
                personalities = []
                for context in contextarray:
                    personalities.append({"path": context["fileName"], "contents": context["fileData"]})
                if len(personalities) > 0:
                    server["personality"] = personalities

            volumearray = server.pop("volumeArray", None)

            VimDriverUtils.replace_key_by_mapping(server,
                                                  self.keys_mapping, True)
            req_body = json.JSONEncoder().encode({"server": server})
            resp = sess.post(req_resouce, data=req_body,
                             endpoint_filter=self.service,
                             headers={"Content-Type": "application/json",
                                      "Accept": "application/json"})

            resp_body = resp.json().pop("server", None)

            logger.debug("Servers--post status::>%s, %s" % (resp_body["id"], resp.status_code))
            if resp.status_code == 200 or resp.status_code == 201 or resp.status_code == 202 :
                if volumearray and len(volumearray) > 0:
                    # server is created, now attach volumes
                    volumeIds = [extraVolume["volumeId"] for extraVolume in volumearray]
                    self.attachVolume(vimid, tenantid, resp_body["id"], *volumeIds)

            metadata = resp_body.pop("metadata", None)
            if metadata:
                meta_data = []
                self.convertMetadata(metadata, meta_data, True)
                resp_body["metadata"] = meta_data

            VimDriverUtils.replace_key_by_mapping(resp_body, self.keys_mapping)
            vim_dict = {
                "vimName": vim["name"],
                "vimId": vim["vimId"],
                "tenantId": tenantid,
                "returnCode": 1,
            }
            resp_body.update(vim_dict)
            resp_body["boot"] = boot
            resp_body["volumeArray"] = volumearray
            resp_body["nicArray"] = nicarray
            resp_body["contextArray"] = contextarray
            resp_body["name"] = servername
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

    def delete(self, request, vimid="", tenantid="", serverid=""):
        logger.debug("Servers--delete::> %s" % request.data)
        try:
            # prepare request resource to vim instance
            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid)

            #check and dettach them if volumes attached to server
            server, status_code = self.get_servers("", vimid, tenantid, serverid)
            volumearray = server.pop("volumeArray", None)
            if volumearray and len(volumearray) > 0:
                volumeIds = [extraVolume["volumeId"] for extraVolume in volumearray]
                self.dettachVolume(vimid, tenantid, serverid, *volumeIds)

            #delete server now
            req_resouce = "servers"
            if serverid:
                req_resouce += "/%s" % serverid

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
