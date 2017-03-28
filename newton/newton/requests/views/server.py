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

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from newton.pub.exceptions import VimDriverNewtonException

from util import VimDriverUtils

logger = logging.getLogger(__name__)


class Servers(APIView):
    service = {'service_type': 'compute',
               'interface': 'public',
               'region_name': 'RegionOne'}
    keys_mapping = [
        ("tenant_id", "tenantId"),
        ("flavorRef", "flavorId"),
        ("user_data", "userdata"),
        ("security_groups", "securityGroups"),
        ("availability_zone ", "availabilityZone"),
    ]

    service_volume = {'service_type': 'volumev2',
                      'interface': 'public',
                      'region_name': 'RegionOne'}

    def attachVolume(self, sess, serverId, volumeId):
        req_resouce = "volumes"
        if volumeId:
            req_resouce += "/%s/action" % volumeId

        req_data = {"os-attach": {
            "instance_uuid": serverId
        }}
        req_body = json.JSONEncoder().encode(req_data)
        resp = sess.post(req_resouce, data=req_body,
                         endpoint_filter=self.service, headers={"Content-Type": "application/json",
                                                                "Accept": "application/json"})
        pass

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

    pass

    def get(self, request, vimid="", tenantid="", serverid=""):
        logger.debug("Servers--get::> %s" % request.data)
        try:
            # prepare request resource to vim instance
            query = VimDriverUtils.get_query_part(request)
            content, status_code = self.get_servers(query, vimid, tenantid, serverid)
            return Response(data=content, status=status_code)
        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
                    pass
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
                server["block_device_mapping_v2 "] = {"uuid": boot["volumeId"],
                                                      "source_type": "volume",
                                                      "destination_type": "volume",
                                                      "delete_on_termination": "false"}
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
                pass

            volumearray = server.pop("volumeArray", None)

            VimDriverUtils.replace_key_by_mapping(server,
                                                  self.keys_mapping, True)
            req_body = json.JSONEncoder().encode({"server": server})
            resp = sess.post(req_resouce, data=req_body,
                             endpoint_filter=self.service, headers={"Content-Type": "application/json",
                                                                    "Accept": "application/json"})

            resp_body = resp.json().pop("server", None)

            if resp.status_code == 201 and volumearray:
                # server is created, now attach volumes
                for volumeId in volumearray:
                    self.attachVolume(sess, resp_body["id"], volumeId)
                    pass

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
            resp_body["volumeArray"] = volumearray
            resp_body["nicArray"] = nicarray
            resp_body["contextArray"] = contextarray
            resp_body["name"] = servername
            return Response(data=resp_body, status=resp.status_code)
        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        pass

    def delete(self, request, vimid="", tenantid="", serverid=""):
        logger.debug("Servers--delete::> %s" % request.data)
        try:
            # prepare request resource to vim instance
            req_resouce = "servers"
            if serverid:
                req_resouce += "/%s" % serverid

            vim = VimDriverUtils.get_vim_info(vimid)
            sess = VimDriverUtils.get_session(vim, tenantid)
            resp = sess.delete(req_resouce, endpoint_filter=self.service)
            return Response(status=resp.status_code)
        except VimDriverNewtonException as e:
            return Response(data={'error': e.content}, status=e.status_code)
        except Exception as e:
            logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        pass
