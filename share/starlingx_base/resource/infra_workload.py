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

import os
import logging
from django.conf import settings

from rest_framework import status
from rest_framework.response import Response
from common.msapi import extsys
from common.msapi.helper import Helper as helper
from common.msapi.helper import MultiCloudThreadHelper

from newton_base.resource import infra_workload as newton_infra_workload
from newton_base.resource import infra_workload_helper as infra_workload_helper

logger = logging.getLogger(__name__)

# global var: Audition thread
# the id is the workloadid, which implies post to workloadid1 followed by delete workloadid1
# will replace the previous backlog item
gInfraWorkloadThread = MultiCloudThreadHelper("infw")

class InfraWorkload(newton_infra_workload.InfraWorkload):
    def __init__(self):
        self._logger = logger

    def post(self, request, vimid="", workloadid=""):
        self._logger.info("vimid: %s, stackid:%s" % (vimid, workloadid))
        self._logger.info("data: %s" % request.data)
        self._logger.debug("META: %s" % request.META)

        resp_template = {
            "template_type": "HEAT",
            "workload_id": workloadid,
            "workload_status": "WORKLOAD_CREATE_FAIL",
            "workload_status_reason": "Exception occurs"
        }
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        try:
            worker_self = InfraWorkloadHelper(
                settings.MULTICLOUD_API_V1_PREFIX,
                settings.AAI_BASE_URL
            )
            if workloadid == "":
                resp_template["workload_status"] = "WORKLOAD_CREATE_FAIL"
                # post to create a new stack, stack id available only after creating a stack is done
                progress_code, progress_status, progress_msg = worker_self.workload_create(vimid, request.data)
                resp_template["workload_status"] = progress_status
                resp_template["workload_status_reason"] = progress_msg

                if progress_code == 0:
                    # update workload_id
                    stack = progress_msg
                    stackid = stack["id"]
                    resp_template["workload_id"] = stackid
                    status_code = status.HTTP_201_CREATED
                else:
                    status_code = status.HTTP_400_BAD_REQUEST

                return Response(data=resp_template, status=status_code)
                # return super(InfraWorkload, self).post(request, vimid)
            else:
                resp_template["workload_status"] = "WORKLOAD_UPDATE_FAIL"
                # a post to heatbridge
                backlog_item = {
                    "id": workloadid,
                    "worker": worker_self.workload_update,
                    "payload": (worker_self, vimid, workloadid, request.data),
                    "repeat": 0,  # one time job
                    # format of status: retcode:0 is ok, otherwise error code from http status, Status ENUM, Message
                    "status": (
                        0, "WORKLOAD_UPDATE_IN_PROGRESS",
                        "backlog to update workload %s pends to schedule" % workloadid
                    )
                }
                gInfraWorkloadThread.add(backlog_item)
                if 0 == gInfraWorkloadThread.state():
                    gInfraWorkloadThread.start()

                # now query the progress
                backlog_item = gInfraWorkloadThread.get(workloadid)
                if not backlog_item:
                    # backlog item not found
                    resp_template["workload_status_reason"] = \
                        "backlog to update workload %s " \
                        "into AAI is not found" % workloadid
                    return Response(
                        data=resp_template,
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                else:
                    progress = backlog_item.get("status",
                                                (13, "WORKLOAD_DELETE_FAIL",
                                                 "Unexpected:status not found in backlog item")
                                                )

                    try:
                        progress_code = progress[0]
                        progress_status = progress[1]
                        progress_msg = progress[2]
                        resp_template["workload_status"] = progress_status
                        resp_template["workload_status_reason"] = progress_msg

                        status_code = status.HTTP_200_ACCEPTED\
                            if progress_code == 0 else progress_code
                    except Exception as e:
                        resp_template["workload_status_reason"] = progress

                    return Response(data=resp_template, status=status_code)
        except Exception as e:
            errmsg = e.message
            self._logger.error(errmsg)
            resp_template["workload_status_reason"] = errmsg
            return Response(data=resp_template,
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, vimid="", workloadid=""):
        self._logger.info("vimid, workload id: %s, %s" % (vimid, workloadid))
        self._logger.debug("META: %s" % request.META)

        resp_template = {
            "template_type": "HEAT",
            "workload_id": workloadid,
            "workload_status": "WORKLOAD_GET_FAIL",
            "workload_status_reason": "Exception occurs"
        }
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        try:

            if workloadid == "":
                resp_template["workload_status_reason"] = "workload id is not found in API url"
                return Response(
                    data=resp_template,
                    status=status.HTTP_400_BAD_REQUEST
                )

            # now query the progress

            backlog_item = gInfraWorkloadThread.get(workloadid)
            if not backlog_item:
                # backlog item not found, so check the stack status
                worker_self = InfraWorkloadHelper(
                    settings.MULTICLOUD_API_V1_PREFIX,
                    settings.AAI_BASE_URL
                )
                progress_code, progress_status, progress_msg = worker_self.workload_status(vimid, workloadid, None)

                resp_template["workload_status"] = progress_status
                resp_template["workload_status_reason"] = progress_msg
                status_code = status.HTTP_200_OK\
                    if progress_code == 0 else progress_code

            else:
                progress = backlog_item.get("status",
                                            (13, "WORKLOAD_DELETE_FAIL",
                                             "Unexpected:status not found in backlog item")
                                            )
                try:
                    progress_code = progress[0]
                    progress_status = progress[1]
                    progress_msg = progress[2]
                    # if gInfraWorkloadThread.expired(workloadid):
                    #     gInfraWorkloadThread.remove(workloadid)
                    resp_template["workload_status"] = progress_status
                    resp_template["workload_status_reason"] = progress_msg
                    status_code = status.HTTP_200_OK\
                        if progress_code == 0 else progress_code
                except Exception as e:
                    resp_template["workload_status_reason"] = progress

            return Response(data=resp_template, status=status_code)

        except Exception as e:
            self._logger.error(e.message)
            resp_template["workload_status_reason"] = e.message
            return Response(data=resp_template,
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, vimid="", workloadid=""):
        self._logger.info("vimid, workload id: %s, %s" % (vimid, workloadid))
        self._logger.debug("META: %s" % request.META)

        resp_template = {
            "template_type": "HEAT",
            "workload_id": workloadid,
            "workload_status": "WORKLOAD_DELETE_FAIL",
            "workload_status_reason": "Exception occurs"
        }
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        try:

            if workloadid == "":
                resp_template["workload_status_reason"] = "workload id is not found in API url"
                return Response(
                    data=resp_template,
                    status=status.HTTP_400_BAD_REQUEST
                )

            # remove the stack object from vim
            super(InfraWorkload, self).delete(request, vimid, workloadid)

            # backlog for a post to heatbridge delete
            worker_self = InfraWorkloadHelper(
                settings.MULTICLOUD_API_V1_PREFIX,
                settings.AAI_BASE_URL
            )
            backlog_item = {
                "id": workloadid,
                "worker": worker_self.workload_delete,
                "payload": (worker_self, vimid, workloadid, request.data),
                "repeat": 0,  # one time job
                # format of status: retcode:0 is ok, otherwise error code from http status, Status ENUM, Message
                "status": (
                    0, "WORKLOAD_DELETE_IN_PROGRESS",
                    "backlog for delete the workload %s "
                    "pends to schedule" % workloadid
                )
            }
            gInfraWorkloadThread.add(backlog_item)
            if 0 == gInfraWorkloadThread.state():
                gInfraWorkloadThread.start()

            # now query the progress
            backlog_item = gInfraWorkloadThread.get(workloadid)
            if not backlog_item:
                # backlog item not found
                resp_template["workload_status_reason"] = \
                    "backlog to remove the "\
                    "workload %s is not found" % workloadid

                return Response(
                    data=resp_template,
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            else:
                progress = backlog_item.get("status",
                                            (13, "WORKLOAD_DELETE_FAIL",
                                             "Unexpected:status not found in backlog item")
                                            )
                try:
                    progress_code = progress[0]
                    progress_status = progress[1]
                    progress_msg = progress[2]
                    # if gInfraWorkloadThread.expired(workloadid):
                    #     gInfraWorkloadThread.remove(workloadid)

                    resp_template["workload_status"] = progress_status
                    resp_template["workload_status_reason"] = progress_msg
                    status_code = status.HTTP_200_ACCEPTED \
                        if progress_code == 0 else progress_code
                except Exception as e:
                    resp_template["workload_status_reason"] = progress
                return Response(data=resp_template, status=status_code)
        except Exception as e:
            self._logger.error(e.message)
            resp_template["workload_status_reason"] = e.message
            return Response(data=resp_template,
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class APIv1InfraWorkload(InfraWorkload):
    def __init__(self):
        super(APIv1InfraWorkload, self).__init__()
        # self._logger = logger

    def post(self, request, cloud_owner="", cloud_region_id=""):
        # self._logger.info("cloud owner, cloud region id, data: %s,%s, %s" %
        #  (cloud_owner, cloud_region_id, request.data))
        # self._logger.debug("META: %s" % request.META)

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1InfraWorkload, self).post(request, vimid)

    def get(self, request, cloud_owner="", cloud_region_id="", requri=""):
        # self._logger.info("cloud owner, cloud region id, data: %s,%s, %s" %
        #  (cloud_owner, cloud_region_id, request.data))
        # self._logger.debug("META: %s" % request.META)

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1InfraWorkload, self).get(request, vimid, requri)

    def delete(self, request, cloud_owner="", cloud_region_id="", requri=""):
        # self._logger.info("cloud owner, cloud region id, data: %s,%s, %s" %
        #  (cloud_owner, cloud_region_id, request.data))
        # self._logger.debug("META: %s" % request.META)

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1InfraWorkload, self).delete(request, vimid, requri)


class InfraWorkloadHelper(infra_workload_helper.InfraWorkloadHelper):

    def __init__(self, multicloud_prefix, aai_base_url):
        super(InfraWorkloadHelper, self).__init__(multicloud_prefix, aai_base_url)
        self._logger = logger

    def param_update_user_directives(self, parameters, oof_directives):
        for attr in oof_directives.get("attributes", []):
            aname = attr.get("attribute_name", None)
            avalue = attr.get("attribute_value", None)
            if aname in parameters:
                parameters[aname] = avalue
            else:
                self._logger.warn(
                    "There is no parameter exist: %s" % aname)

        return parameters

    def param_update_sdnc_directives(self, parameters, sdnc_directives):
        for attr in sdnc_directives.get("attributes", []):
            aname = attr.get("attribute_name", None)
            avalue = attr.get("attribute_value", None)
            if aname in parameters:
                parameters[aname] = avalue
            else:
                self._logger.warn(
                    "There is no parameter exist: %s" % aname)

        return parameters

    def param_update_oof_directives(self, parameters, oof_directives):
        for directive in oof_directives.get("directives", []):
            if directive["type"] == "vnfc":
                for directive2 in directive.get("directives", []):
                    if directive2["type"] in ["flavor_directives",
                                              "sriovNICNetwork_directives"]:
                        for attr in directive2.get("attributes", []):
                            flavor_label = attr.get("attribute_name", None)
                            flavor_value = attr.get("attribute_value", None)
                            if flavor_label in parameters:
                                parameters[flavor_label] = flavor_value
                            else:
                                self._logger.warn(
                                    "There is no parameter exist: %s" %
                                    flavor_label)

        return parameters

    def openstack_template_update(self, template_data, vf_module_model_customization_id):
        # try 1: check if artifact is available with vfmodule_uuid
        # assumption: mount point: /opt/artifacts/<vfmodule_uuid>
        try:
            vfmodule_path_base = r"/opt/artifacts/%s" % vf_module_model_customization_id
            vfmodule_metadata_path = r"%s/vfmodule-meta.json" % vfmodule_path_base
            service_metadata_path = r"%s/service-meta.json" % vfmodule_path_base
            with open(vfmodule_metadata_path,
                      'r', encoding='UTF-8') as vf:
                vfmodule_metadata = vf.read()  # assume the metadata file size is small
                if vfmodule_metadata and len(vfmodule_metadata) > 0:
                    # load service-metadata
                    with open(service_metadata_path,
                              'r', encoding='UTF-8') as sf:
                        service_metadata = sf.read()  # assume the metadata file size is small
                        if service_metadata and len(service_metadata) > 0:
                            # get the artifacts uuid
                            artifacts_uuids = vfmodule_metadata.get("artifacts", None)
                            templatedata1 = {}.update(template_data)
                            for a in service_metadata["artifacts"]:
                                artifactUUID = a.get("artifactUUID", "")
                                if artifactUUID not in artifacts_uuids:
                                    continue
                                artifact_type = a.get("artifactType", "")
                                artifact_name = a.get("artifactName", "")
                                artifact_path = r"%s/%s" % (vfmodule_path_base, artifact_name)

                                # now check the type
                                if artifact_type.lower() == "heat":
                                    # heat template file
                                    with open(artifact_path,
                                              'r', encoding='UTF-8') as af:
                                        templatedata1["template"] = af.read()  # assume the template file size is small
                                    # pass

                                elif artifact_type.lower() == "heat_env":
                                    # heat env file
                                    with open(artifact_path,
                                              'r', encoding='UTF-8') as af:
                                        templatedata1["parameters"] = af.read()  # assume the env file size is small
                                    # pass
                                # pass
                            return templatedata1
                        else:
                            pass
                else:
                    self._logger.info("artifacts not available for vfmodule %s" % vfmodule_uuid)
                    pass
        except Exception as e:
            self._logger.error("template_update fails: %s" % e.message)

        # try 2: reuse the input: template_data
        return template_data

    def workload_create(self, vimid, workload_data):
        '''
        Instantiate a stack over target cloud region (OpenStack instance)
        The template for workload will be fetched from sdc client
        :param vimid:
        :param workload_data:
        :return: result code, status enum, status reason
            result code: 0-ok, otherwise error
            status enum: "WORKLOAD_CREATE_IN_PROGRESS", "WORKLOAD_CREATE_FAIL"
            status reason: message to explain the status enum
        '''

        # step 2: normalize the input: xxx_directives
        data = workload_data
        vf_module_model_customization_id = data.get("vf-module-model-customization-id", None)
        vf_module_id = data.get("vf-module-id", "")
        user_directive = data.get("user_directives", {})
        oof_directive = data.get("oof_directives", {})
        sdnc_directive = data.get("sdnc_directives", {})
        template_type = data.get("template_type", None)
        template_data = data.get("template_data", {})
        # resp_template = None
        if not template_type or "heat" != template_type.lower():
            return 14, "WORKLOAD_CREATE_FAIL", \
                   "Bad parameters: template type %s is not heat" %\
                   template_type or ""

        # retrieve the template data
        template_data = self.openstack_template_update(template_data, vf_module_model_customization_id)

        # update the parameter in order of reverse precedence
        parameters = template_data.get("parameters", {})
        parameters = self.param_update_sdnc_directives(parameters, sdnc_directive)
        parameters = self.param_update_oof_directives(parameters, oof_directive)
        parameters = self.param_update_user_directives(parameters, user_directive)
        template_data["parameters"] = parameters

        # reset to make sure "files" are empty
        template_data["files"] = {}

        template_data["stack_name"] = vf_module_id \
            if not hasattr(template_data, "stack_name")\
            else template_data["stack_name"]

        # authenticate
        cloud_owner, regionid = extsys.decode_vim_id(vimid)
        # should go via multicloud proxy so that
        #  the selflink is updated by multicloud
        retcode, v2_token_resp_json, os_status = \
            helper.MultiCloudIdentityHelper(
                settings.MULTICLOUD_API_V1_PREFIX,
                cloud_owner, regionid, "/v2.0/tokens"
            )
        if retcode > 0 or not v2_token_resp_json:
            errmsg = "authenticate fails:%s,%s, %s" %\
                     (cloud_owner, regionid, v2_token_resp_json)
            logger.error(errmsg)
            return (
                retcode, "WORKLOAD_CREATE_FAIL", errmsg
            )

        # tenant_id = v2_token_resp_json["access"]["token"]["tenant"]["id"]
        service_type = "orchestration"
        resource_uri = "/stacks"
        self._logger.info("create stack resources, URI:%s" % resource_uri)
        retcode, content, os_status = \
            helper.MultiCloudServiceHelper(cloud_owner, regionid,
                                           v2_token_resp_json,
                                           service_type, resource_uri,
                                           template_data, "POST")

        if retcode == 0:
            stack1 = content.get('stack', None)
            # stackid = stack1["id"] if stack1 else ""
            return 0, "WORKLOAD_CREATE_IN_PROGRESS", stack1
        else:
            self._logger.info("RESP with data> result:%s" % content)
            return retcode, "WORKLOAD_CREATE_FAIL", content
