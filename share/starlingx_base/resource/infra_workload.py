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
import json

import logging
from django.conf import settings
from django.http import QueryDict
from rest_framework import status
from rest_framework.response import Response
from common.msapi import extsys
from common.msapi.helper import Helper as helper
from common.msapi.helper import MultiCloudThreadHelper

from newton_base.resource import infra_workload as newton_infra_workload
from newton_base.resource import infra_workload_helper as infra_workload_helper

from newton_base.util import VimDriverUtils

import yaml
NoDatesSafeLoader = yaml.SafeLoader
NoDatesSafeLoader.yaml_implicit_resolvers = {
    k: [r for r in v if r[0] != 'tag:yaml.org,2002:timestamp'] for
        k, v in NoDatesSafeLoader.yaml_implicit_resolvers.items()
}

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

        # Get the specified tenant id
        specified_project_idorname = request.META.get("Project", None)

        resp_template = {
            "template_type": "HEAT",
            "workload_id": workloadid,
            "workload_status": "CREATE_FAILED",
            "workload_status_reason": "Exception occurs"
        }
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        try:
            worker_self = InfraWorkloadHelper(
                settings.MULTICLOUD_API_V1_PREFIX,
                settings.AAI_BASE_URL
            )
            if workloadid == "":
                resp_template["workload_status"] = "CREATE_FAILED"
                # post to create a new stack,
                # stack id available only after creating a stack is done
                progress_code, progress_status, progress_msg =\
                    worker_self.workload_create(vimid, request.data, specified_project_idorname)
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
                resp_template["workload_status"] = "UPDATE_FAILED"
                # a post to heatbridge
                backlog_item = {
                    "id": workloadid,
                    "worker": worker_self.workload_update,
                    "payload": (vimid, workloadid,
                                request.data, specified_project_idorname),
                    "repeat": 0,  # one time job
                    # format of status: retcode:0 is ok, otherwise error code from http status, Status ENUM, Message
                    "status": (
                        0, "UPDATE_IN_PROGRESS",
                        "backlog to update workload %s is on progress" % workloadid
                    )
                }
                gInfraWorkloadThread.add(backlog_item)
                if 0 == gInfraWorkloadThread.state():
                    gInfraWorkloadThread.start()
                # progress = worker_self.workload_update(
                #     vimid, workloadid,
                #     request.data, specified_project_idorname)
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
                    progress = backlog_item.get(
                        "status",
                        (13, "UPDATE_FAILED",
                         "Unexpected:status not found in backlog item")
                    )

                    try:
                        progress_code = progress[0]
                        progress_status = progress[1]
                        progress_msg = progress[2]
                        resp_template["workload_status"] = progress_status
                        resp_template["workload_status_reason"] = progress_msg

                        status_code = status.HTTP_202_ACCEPTED\
                            if progress_code == 0 else progress_code
                    except Exception as e:
                        self._logger.warn("Exception: %s" % e.message)
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

        # Get the specified tenant id
        specified_project_idorname = request.META.get("Project", None)

        resp_template = {
            "template_type": "HEAT",
            "workload_id": workloadid,
            "workload_status": "GET_FAILED",
            "workload_status_reason": "Exception occurs"
        }
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        try:

            if workloadid == "":
                # now check the query params in case of query existing of workload
                querystr = request.META.get("QUERY_STRING", None)
                qd = QueryDict(querystr).dict() if querystr else None
                workload_query_name = qd.get("name", None) if qd else None
                workload_query_id = qd.get("id", None) if qd else None

                if not workload_query_name and not workload_query_id:
                    resp_template["workload_status_reason"] =\
                        "workload id is not found in API url"
                    return Response(
                        data=resp_template,
                        status=status.HTTP_400_BAD_REQUEST
                    )
                else:
                    worker_self = InfraWorkloadHelper(
                        settings.MULTICLOUD_API_V1_PREFIX,
                        settings.AAI_BASE_URL
                    )

                    # now query the status of workload by name or id, id as 1st priority
                    progress_code, progress_status, progress_msg =\
                        0, "GET_FAILED", ""
                    if workload_query_id:
                        # by id
                        progress_code, progress_status, progress_msg =\
                            worker_self.workload_status(
                                vimid, stack_id=workload_query_id,
                                project_idorname=specified_project_idorname
                            )
                    else:
                        # by name or get all stacks
                        progress_code, progress_status, progress_msg =\
                            worker_self.workload_status(
                                vimid, stack_name=workload_query_name,
                                project_idorname=specified_project_idorname
                            )

                    resp_template["workload_status"] = progress_status
                    resp_template["workload_status_reason"] = progress_msg
                    status_code = status.HTTP_200_OK \
                        if progress_code == 0 else status.HTTP_500_INTERNAL_SERVER_ERROR  # progress_code

                    pass

            else:
                # now query the progress
                backlog_item = gInfraWorkloadThread.get(workloadid)
                if not backlog_item:
                    # backlog item not found, so check the stack status
                    worker_self = InfraWorkloadHelper(
                        settings.MULTICLOUD_API_V1_PREFIX,
                        settings.AAI_BASE_URL
                    )
                    progress_code, progress_status, progress_msg =\
                        worker_self.workload_detail(
                            vimid, stack_id=workloadid,
                            project_idorname=specified_project_idorname)

                    resp_template["workload_status"] = progress_status
                    resp_template["workload_status_reason"] = progress_msg
                    status_code = status.HTTP_200_OK\
                        if progress_code == 0 else progress_code

                else:
                    progress = backlog_item.get(
                        "status",
                        (13, "GET_FAILED",
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

        # Get the specified tenant id
        specified_project_idorname = request.META.get("Project", None)

        resp_template = {
            "template_type": "HEAT",
            "workload_id": workloadid,
            "workload_status": "DELETE_FAILED",
            "workload_status_reason": "Exception occurs"
        }
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        try:

            if workloadid == "":
                resp_template["workload_status_reason"] =\
                    "workload id is not found in API url"
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
                "payload": (vimid, workloadid, request.data,
                            specified_project_idorname),
                "repeat": 0,  # one time job
                # format of status: retcode:0 is ok, otherwise error code from http status, Status ENUM, Message
                "status": (
                    0, "DELETE_IN_PROGRESS",
                    "backlog for delete the workload %s "
                    "is on progress" % workloadid
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
                progress = backlog_item.get(
                    "status",
                    (13, "DELETE_FAILED",
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
                    status_code = status.HTTP_202_ACCEPTED \
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

    def post(self, request, cloud_owner="", cloud_region_id="", workloadid=""):
        # self._logger.info("cloud owner, cloud region id, data: %s,%s, %s" %
        #  (cloud_owner, cloud_region_id, request.data))
        # self._logger.debug("META: %s" % request.META)

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1InfraWorkload, self).post(request, vimid, workloadid)

    def get(self, request, cloud_owner="", cloud_region_id="", workloadid=""):
        # self._logger.info("cloud owner, cloud region id, data: %s,%s, %s" %
        #  (cloud_owner, cloud_region_id, request.data))
        # self._logger.debug("META: %s" % request.META)

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1InfraWorkload, self).get(request, vimid, workloadid)

    def delete(self, request, cloud_owner="", cloud_region_id="", workloadid=""):
        # self._logger.info("cloud owner, cloud region id, data: %s,%s, %s" %
        #  (cloud_owner, cloud_region_id, request.data))
        # self._logger.debug("META: %s" % request.META)

        vimid = extsys.encode_vim_id(cloud_owner, cloud_region_id)
        return super(APIv1InfraWorkload, self).delete(request, vimid, workloadid)


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
            self._logger.debug("vfmodule_path_base: %s" % vfmodule_path_base)
            vfmodule_metadata_path = r"%s/vfmodule-meta.json" % vfmodule_path_base
            service_metadata_path = r"%s/service-meta.json" % vfmodule_path_base
            with open(vfmodule_metadata_path,
                      'r') as vf:
                vfmodule_metadata_str = vf.read()  # assume the metadata file size is small
                vfmodule_metadata = json.loads(vfmodule_metadata_str)
                vfmodule_metadata = [e for e in vfmodule_metadata
                                     if e.get("vfModuleModelCustomizationUUID", None)
                                     == vf_module_model_customization_id]
                self._logger.debug("vfmodule_metadata: %s" % vfmodule_metadata)
                if vfmodule_metadata and len(vfmodule_metadata) > 0:
                    # load service-metadata
                    with open(service_metadata_path,
                              'r') as sf:
                        service_metadata_str = sf.read()  # assume the metadata file size is small
                        service_metadata = json.loads(service_metadata_str)
                        self._logger.debug("service_metadata: %s" % service_metadata)
                        if service_metadata and len(service_metadata) > 0:
                            # get the artifacts uuid
                            artifacts_uuids = vfmodule_metadata[0].get("artifacts", None)
                            self._logger.debug("artifacts_uuids: %s" % artifacts_uuids)
                            templatedata1 = template_data.copy()
                            for a in service_metadata["artifacts"]:
                                artifactUUID = a.get("artifactUUID", "")
                                if artifactUUID not in artifacts_uuids:
                                    continue
                                artifact_type = a.get("artifactType", "")
                                artifact_name = a.get("artifactName", "")
                                artifact_path = r"%s/%s" % (vfmodule_path_base, artifact_name)
                                self._logger.debug("artifact_path: %s" % artifact_path)

                                # now check the type
                                if artifact_type.lower() == "heat":
                                    # heat template file
                                    with open(artifact_path,
                                              'r') as af:
                                        # assume the template file size is small
                                        templatedata1["template"] = \
                                            yaml.load(af, Loader=NoDatesSafeLoader)
                                    # pass

                                elif artifact_type.lower() == "heat_env":
                                    # heat env file
                                    with open(artifact_path,
                                              'r') as af:
                                        # assume the env file size is small
                                        templatedata1.update(yaml.load(
                                            af, Loader=NoDatesSafeLoader))
                                    # pass
                                # pass
                            return templatedata1
                        else:
                            pass
                else:
                    self._logger.info("artifacts not available for vfmodule %s" % vf_module_model_customization_id)
                    pass
        except Exception as e:
            self._logger.error("template_update fails: %s" % e.message)

        # try 2: reuse the input: template_data
        return template_data

    def workload_create(self, vimid, workload_data, project_idorname=None):
        '''
        Instantiate a stack over target cloud region (OpenStack instance)
        The template for workload will be fetched from sdc client
        :param vimid:
        :param workload_data:
        :param project_idorname: tenant id or name
        :return: result code, status enum, status reason
            result code: 0-ok, otherwise error
            status enum: "CREATE_IN_PROGRESS", "CREATE_FAILED"
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
            return status.HTTP_400_BAD_REQUEST, "CREATE_FAILED", \
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

        template_data["stack_name"] =\
            template_data.get("stack_name", vf_module_id)

        # authenticate
        cloud_owner, regionid = extsys.decode_vim_id(vimid)
        # should go via multicloud proxy so that
        #  the selflink is updated by multicloud
        retcode, v2_token_resp_json, os_status = \
            helper.MultiCloudIdentityHelper(
                settings.MULTICLOUD_API_V1_PREFIX,
                cloud_owner, regionid, "/v2.0/tokens",
                {"Project": project_idorname}
            )
        if retcode > 0 or not v2_token_resp_json:
            errmsg = "authenticate fails:%s,%s, %s" %\
                     (cloud_owner, regionid, v2_token_resp_json)
            logger.error(errmsg)
            return (
                os_status, "CREATE_FAILED", errmsg
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
            return 0, "CREATE_IN_PROGRESS", stack1
        else:
            self._logger.info("workload_create fails: %s" % content)
            return os_status, "CREATE_FAILED", content
