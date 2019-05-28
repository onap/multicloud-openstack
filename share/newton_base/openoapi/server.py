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
import threading
import traceback

from keystoneauth1.exceptions import HttpError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import VimDriverNewtonException
from newton_base.util import VimDriverUtils
from common.msapi import extsys

logger = logging.getLogger(__name__)

running_threads = {}
running_thread_lock = threading.Lock()


# assume volume is attached on server creation
class ServerVolumeAttachThread (threading.Thread):
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
        if self.is_attach:
            self.attach_volume(self.vimid, self.tenantid, self.serverid, *self.volumeids)
        else:
            self.detach_volume(self.vimid, self.tenantid, self.serverid, *self.volumeids)
        logger.debug("stop server thread %s, %s, %s" % (self.vimid, self.tenantid, self.serverid))
        running_thread_lock.acquire()
        running_threads.pop(self.serverid)
        running_thread_lock.release()

    def attach_volume(self, vimid, tenantid, serverid, *volumeids):
        logger.info("vimid, tenantid, serverid, volumeids = %s,%s,%s,%s" % (vimid, tenantid, serverid, volumeids))
        try:
            # prepare request resource to vim instance
            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid)

            self.service['region_name'] = vim['openstack_region_id'] \
                if vim.get('openstack_region_id') \
                else vim['cloud_region_id']

            # check if server is ready to attach
            logger.debug("Servers--attach_volume, wait for server to be ACTIVE::>%s" % serverid)
            req_resouce = "servers/%s" % serverid
            while True:
                logger.info("making request with URI:%s" % req_resouce)
                resp = sess.get(req_resouce, endpoint_filter=self.service)
                if resp.status_code == status.HTTP_200_OK:
                    logger.debug("with content:%s" % resp.json())
                    pass

                content = resp.json()
                if content and content["server"] and content["server"]["status"] == "ACTIVE":
                    break

            for volumeid in volumeids:
                req_resouce = "servers/%s/os-volume_attachments" % serverid
                req_data = {"volumeAttachment": {
                    "volumeId": volumeid
                }}
                logger.debug("Servers--attach_volume::>%s, %s" % (req_resouce, req_data))
                req_body = json.JSONEncoder().encode(req_data)
                logger.info("making request with URI:%s" % req_resouce)
                resp = sess.post(req_resouce, data=req_body,
                                 endpoint_filter=self.service,
                                 headers={"Content-Type": "application/json",
                                          "Accept": "application/json"})
                logger.info("request returns with status %s" % resp.status_code)
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

            self.service['region_name'] = vim['openstack_region_id'] \
                if vim.get('openstack_region_id') \
                else vim['cloud_region_id']

            # wait server to be ready to detach volume

            # assume attachment id is the same as volume id
            for volumeid in volumeids:
                req_resouce = "servers/%s/os-volume_attachments/%s" % (serverid, volumeid)

                logger.info("making request with URI:%s" % req_resouce)
                resp = sess.delete(req_resouce,
                                   endpoint_filter=self.service,
                                   headers={"Content-Type": "application/json",
                                            "Accept": "application/json"})
                logger.info("request returns with status %s" % resp.status_code)
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

    def __init__(self):
        super(Servers, self).__init__()
        self._logger = logger

    def _attach_volume(self, vimid, tenantid, serverId, *volumeIds):
        # has to be async mode to wait server is ready to attach volume
        logger.debug("launch thread to attach volume: %s" % serverId)
        tmp_thread = ServerVolumeAttachThread(vimid, tenantid, serverId, True, *volumeIds)
        running_thread_lock.acquire()
        running_threads[serverId] = tmp_thread
        running_thread_lock.release()
        tmp_thread.start()

    def _dettach_volume(self, vimid, tenantid, serverId, *volumeIds):
        # assume attachment id is the same as volume id
        vim = VimDriverUtils.get_vim_info(vimid)
        sess = VimDriverUtils.get_session(vim, tenantid)

        self.service['region_name'] = vim['openstack_region_id'] \
            if vim.get('openstack_region_id') \
            else vim['cloud_region_id']

        for volumeid in volumeIds:
            req_resouce = "servers/%s/os-volume_attachments/%s" % (serverId, volumeid)
            logger.debug("Servers--dettachVolume::>%s" % req_resouce)
            logger.info("making request with URI:%s" % req_resouce)
            resp = sess.delete(req_resouce,
                               endpoint_filter=self.service,
                               headers={"Content-Type": "application/json",
                                        "Accept": "application/json"})
            logger.info("request returns with status %s" % resp.status_code)
            logger.debug("Servers--dettachVolume resp status::>%s" % resp.status_code)

    # def _convert_metadata(self, metadata_vfc, metadata_openstack, reverse=True):
    #    if not reverse:
    #        # from vfc format to openstack format
    #        for spec in metadata_vfc:
    #            metadata_openstack[spec['keyName']] = spec['value']
    #    else:
    #        for k, v in metadata_openstack.items():
    #            spec = {}
    #            spec['keyName'] = k
    #            spec['value'] = v
    #            metadata_vfc.append(spec)

    def _convert_resp(self, server):
        # convert volumeArray
        volumeArray = server.pop("volumeArray", None)
        tmpVolumeArray = []
        if volumeArray and len(volumeArray) > 0:
            for vol in volumeArray:
                tmpVolumeArray.append({"volumeId": vol["id"]})
        server["volumeArray"] = tmpVolumeArray if len(tmpVolumeArray) > 0 else None

        # convert flavor
        flavor = server.pop("flavor", None)
        server["flavorId"] = flavor["id"] if flavor else None

        # convert nicArray

        # convert boot
        imageObj = server.pop("image", None)
        imageId = imageObj.pop("id", None) if imageObj else None
        if imageId:
            server["boot"] = {"type":2, "imageId": imageId}
        else:
            server["boot"] = {
                "type": 1,
                "volumeId": tmpVolumeArray.pop(0)["volumeId"]
                if len(tmpVolumeArray) > 0 else None
            }

        # convert OS-EXT-AZ:availability_zone
        server["availabilityZone"] = server.pop("OS-EXT-AZ:availability_zone", None)

    def get(self, request, vimid="", tenantid="", serverid=""):
        logger.info("vimid, tenantid, serverid = %s,%s,%s" % (vimid, tenantid, serverid))
        if request.data:
            logger.debug("With data = %s" % request.data)
            pass
        try:
            # prepare request resource to vim instance
            query = VimDriverUtils.get_query_part(request)
            content, status_code = self._get_servers(query, vimid, tenantid, serverid)
            return Response(data=content, status=status_code)
        except VimDriverNewtonException as e:
            logger.error("response with status = %s" % e.status_code)
            return Response(data={'error': e.content}, status=e.status_code)
        except HttpError as e:
            logger.error("HttpError: status:%s, response:%s"
                         % (e.http_status, e.response.json()))
            return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_ports(self, vimid="", tenantid="", serverid=None):
        # query attached ports
        vim = VimDriverUtils.get_vim_info(vimid)
        sess = VimDriverUtils.get_session(vim, tenantid)
        req_resouce = "servers/%s/os-interface" % serverid

        self.service['region_name'] = vim['openstack_region_id'] \
            if vim.get('openstack_region_id') \
            else vim['cloud_region_id']

        logger.info("making request with URI:%s" % req_resouce)
        resp = sess.get(req_resouce, endpoint_filter=self.service)
        logger.info("request returns with status %s" % resp.status_code)
        if resp.status_code == status.HTTP_200_OK:
            logger.debug("with content:%s" % resp.json())
            pass
        ports = resp.json()
        if ports and ports["interfaceAttachments"] \
                and len(ports["interfaceAttachments"]) > 0:
            return [{"portId":port["port_id"]}
                    for port in ports["interfaceAttachments"]]
        return None

    def _get_servers(self, query="", vimid="", tenantid="", serverid=None):
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

        if not serverid:
            # convert the key naming in servers
            for server in content["servers"]:
                # metadata_openstack = server.pop("metadata", None)
                # if metadata_openstack:
                #    metadata_vfc = []
                #    self._convert_metadata(metadata_vfc, metadata_openstack, True)
                #    server["metadata"] = metadata_vfc
                VimDriverUtils.replace_key_by_mapping(server,
                                                      self.keys_mapping)
                self._convert_resp(server)
                server["nicArray"] = self._get_ports(vimid, tenantid, server["id"])

        else:
            # convert the key naming in the server specified by id
            server = content.pop("server", None)
            # metadata_openstack = server.pop("metadata", None)
            # if metadata_openstack:
            #    metadata_vfc = []
            #    self._convert_metadata(metadata_vfc, metadata_openstack, True)
            #    server["metadata"] = metadata_vfc
            VimDriverUtils.replace_key_by_mapping(server,
                                                  self.keys_mapping)
            self._convert_resp(server)
            server["nicArray"] = self._get_ports(vimid, tenantid, serverid)
            content.update(server)

        return content, resp.status_code

    def post(self, request, vimid="", tenantid="", serverid=""):
        logger.info("vimid, tenantid, serverid = %s,%s,%s" % (vimid, tenantid, serverid))
        if request.data:
            logger.debug("With data = %s" % request.data)
            pass
        try:
            # check if created already: check name
            servername = request.data["name"]
            query = "name=%s" % servername
            content, status_code = self._get_servers(query, vimid, tenantid)
            logger.info("content %s" % content)
            existed = False
            if status_code == status.HTTP_200_OK:
                for server in content["servers"]:
                    if server["name"] == request.data["name"]:
                        existed = True
                        break
                if existed and server:
                    vim_dict = {
                        "returnCode": 0,
                    }
                    server.update(vim_dict)
                    return Response(data=server, status=status_code)

            # prepare request resource to vim instance
            req_resouce = "servers"
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
            networks = []
            for nic in nicarray:
                networks.append({"port": nic["portId"]})
            if len(networks) > 0:
                server["networks"] = networks

            # metadata_vfc = server.pop("metadata", None)
            # if metadata_vfc:
            #    metadata_openstack = {}
            #    self._convert_metadata(metadata_vfc, metadata_openstack, True)
            #    server["metadata"] = metadata_openstack

            contextarray = server.pop("contextArray", None)
            volumearray = server.pop("volumeArray", None)

            # inject files
            logger.info("Start inject files contextarray %s" % contextarray)
            if contextarray is not None:
                if isinstance(contextarray, list):
                    personalities = []
                    for context in contextarray:
                        personality = {}
                        personality["path"] = context["dest_path"]
                        personality["contents"] = context["source_data_base64"]
                        personalities.append(personality)

                    if len(personalities) > 0:
                        server["personality"] = personalities
                    logger.info("List personalities %s" % personalities)
                elif isinstance(contextarray, dict):
                    personalities = []
                    personality = {}
                    context = contextarray
                    personality["path"] = context["dest_path"]
                    personality["contents"] = context["source_data_base64"]
                    personalities.append(personality)

                    if len(personalities) > 0:
                        server["personality"] = personalities
                    logger.info("Personalities %s" % personalities)
                else:
                    errmsg = "contextarray %s format is not right." % contextarray
                    logger.error(errmsg)
                    return Response(data={'error': errmsg},
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            VimDriverUtils.replace_key_by_mapping(server,
                                                  self.keys_mapping, True)
            req_body = json.JSONEncoder().encode({"server": server})
            logger.info("-server %s, json_server %s" % (server, req_body))
            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid)

            self.service['region_name'] = vim['openstack_region_id'] \
                if vim.get('openstack_region_id') \
                else vim['cloud_region_id']
            logger.info("making request with URI:%s" % req_resouce)
            resp = sess.post(req_resouce, data=req_body,
                             endpoint_filter=self.service,
                             headers={"Content-Type": "application/json",
                                      "Accept": "application/json"})
            logger.info("request returns with status %s" % resp.status_code)
            resp_body = resp.json().pop("server", None)

            logger.debug("Servers--post status::>%s, %s" % (resp_body["id"], resp.status_code))
            if resp.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED, status.HTTP_202_ACCEPTED]:
                if volumearray and len(volumearray) > 0:
                    # server is created, now attach volumes
                    volumeIds = [extraVolume["volumeId"] for extraVolume in volumearray]
                    self._attach_volume(vimid, tenantid, resp_body["id"], *volumeIds)

            # metadata_openstack = resp_body.pop("metadata", None)
            # if metadata_openstack:
            #    metadata_vfc = []
            #    self._convert_metadata(metadata_vfc, metadata_openstack, True)
            #    resp_body["metadata"] = metadata_vfc

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
            resp_body["boot"] = boot
            resp_body["volumeArray"] = volumearray
            resp_body["nicArray"] = nicarray
            resp_body["contextArray"] = contextarray
            resp_body["name"] = servername
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

    def delete(self, request, vimid="", tenantid="", serverid=""):
        logger.info("vimid, tenantid, serverid = %s,%s,%s" % (vimid, tenantid, serverid))
        if request.data:
            logger.debug("With data = %s" % request.data)
            pass
        try:
            # prepare request resource to vim instance
            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid)

            self.service['region_name'] = vim['openstack_region_id'] \
                if vim.get('openstack_region_id') \
                else vim['cloud_region_id']

            # check and dettach them if volumes attached to server
            server, status_code = self._get_servers("", vimid, tenantid, serverid)
            volumearray = server.pop("volumeArray", None)
            if volumearray and len(volumearray) > 0:
                volumeIds = [extraVolume["volumeId"] for extraVolume in volumearray]
                self._dettach_volume(vimid, tenantid, serverid, *volumeIds)

            # delete server now
            req_resouce = "servers"
            if serverid:
                req_resouce += "/%s" % serverid
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

class APIv1Servers(Servers):

    def __init__(self):
        super(APIv1Servers, self).__init__()
        self._logger = logger

    def get(self, request, cloud_owner="", cloud_region_id="", tenantid="", serverid=""):
        self._logger.info("%s, %s" % (cloud_owner, cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1Servers, self).get(request, vimid, tenantid, serverid)

    def post(self, request, cloud_owner="", cloud_region_id="", tenantid="", serverid=""):
        self._logger.info("%s, %s" % (cloud_owner, cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1Servers, self).post(request, vimid, tenantid, serverid)

    def delete(self, request, cloud_owner="", cloud_region_id="", tenantid="", serverid=""):
        self._logger.info("%s, %s" % (cloud_owner, cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1Servers, self).delete(request, vimid, tenantid, serverid)


class ServerAction(APIView):
    service = {'service_type': 'compute',
               'interface': 'public'}

    def __init__(self):
        super(ServerAction, self).__init__()
        self._logger = logger

    def post(self, request, vimid="", tenantid="", serverid=""):
        logger.debug("ServerAction--post::> %s" % request.data)
        logger.debug("vimid=%s, tenantid=%s, serverid=%s", vimid, tenantid, serverid)
        try:
            # prepare request resource to vim instance
            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid)

            # operate server now
            req_resouce = "servers/{server_id}/action".format(server_id=serverid)
            req_body = json.JSONEncoder().encode(request.data)
            resp = sess.post(req_resouce, data=req_body,
                             endpoint_filter=self.service,
                             headers={"Content-Type": "application/json",
                                      "Accept": "application/json"})
            resp_body = resp.json()

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


class APIv1ServerAction(ServerAction):

    def __init__(self):
        super(APIv1ServerAction, self).__init__()
        self._logger = logger

    def post(self, request, cloud_owner="", cloud_region_id="", tenantid="", serverid=""):
        self._logger.info("%s, %s" % (cloud_owner, cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1ServerAction, self).post(request, vimid, tenantid, serverid)


class ServerOsInterface(APIView):
    service = {'service_type': 'compute',
               'interface': 'public'}


    def __init__(self):
        super(ServerOsInterface, self).__init__()
        self._logger = logger

    def post(self, request, vimid="", tenantid="", serverid=""):
        logger.debug("ServerOsInterface--post::> %s" % request.data)
        logger.debug("vimid=%s, tenantid=%s, serverid=%s", vimid, tenantid, serverid)
        try:
            # prepare request resource to vim instance
            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid)

            # operate server now
            req_resouce = "servers/{server_id}/os-interface".format(server_id=serverid)
            req_body = json.JSONEncoder().encode(request.data)
            resp = sess.post(req_resouce, data=req_body,
                             endpoint_filter=self.service,
                             headers={"Content-Type": "application/json",
                                      "Accept": "application/json"})
            resp_body = resp.json()

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


class APIv1ServerOsInterface(ServerOsInterface):

    def __init__(self):
        super(APIv1ServerOsInterface, self).__init__()
        self._logger = logger

    def post(self, request, cloud_owner="", cloud_region_id="", tenantid="", serverid=""):
        self._logger.info("%s, %s" % (cloud_owner, cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1ServerOsInterface, self).post(request, vimid, tenantid, serverid)


class ServerOsInterfacePort(APIView):
    service = {'service_type': 'compute',
               'interface': 'public'}

    def __init__(self):
        super(ServerOsInterfacePort, self).__init__()
        self._logger = logger

    def delete(self, request, vimid="", tenantid="", serverid="", portid=""):
        logger.debug("ServerOsInterfacePort--delete::portid=%s", portid)
        logger.debug("vimid=%s, tenantid=%s, serverid=%s", vimid, tenantid, serverid)
        try:
            # prepare request resource to vim instance
            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid)

            # operate server now
            req_resfmt = "servers/{server_id}/os-interface/{port_id}"
            req_resouce = req_resfmt.format(server_id=serverid, port_id=portid)
            resp = sess.delete(req_resouce,
                             endpoint_filter=self.service,
                             headers={"Content-Type": "application/json",
                                      "Accept": "application/json"})
            resp_body = {}

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


class APIv1ServerOsInterfacePort(ServerOsInterfacePort):

    def __init__(self):
        super(APIv1ServerOsInterfacePort, self).__init__()
        self._logger = logger

    def delete(self, request, cloud_owner="", cloud_region_id="", tenantid="", serverid="", portid=""):
        self._logger.info("%s, %s" % (cloud_owner, cloud_region_id))

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1ServerOsInterfacePort, self).post(request, vimid, tenantid, serverid, portid)
