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
from starlingx_base.resource import openstack_infra_workload_helper
from starlingx_base.resource import k8s_infra_workload_helper

from newton_base.util import VimDriverUtils

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
            "workload_status": "CREATE_FAILED",
            "workload_status_reason": "Exception occurs"
        }
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        # check if target to k8s
        viminfo = VimDriverUtils.get_vim_info(vimid)
        if VimDriverUtils.check_k8s_cluster(viminfo):
            try:
                # wrap call to multicloud-k8s
                return k8s_infra_workload_helper.InfraWorkloadHelper.workload_create(
                    self, vimid, workloadid, request)
            except Exception as e:
                errmsg = str(e)
                self._logger.error(errmsg)
                resp_template["workload_status_reason"] = errmsg
                return Response(data=resp_template,
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # otherwise, target to openstack
        # Get the specified tenant id
        specified_project_idorname = request.META.get("Project", None)

        try:
            worker_self = openstack_infra_workload_helper.InfraWorkloadHelper(
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
                        self._logger.warn("Exception: %s" % str(e))
                        resp_template["workload_status_reason"] = progress

                    return Response(data=resp_template, status=status_code)
        except Exception as e:
            errmsg = str(e)
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
            "workload_status": "GET_FAILED",
            "workload_status_reason": "Exception occurs"
        }
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        # check if target to k8s
        viminfo = VimDriverUtils.get_vim_info(vimid)
        if VimDriverUtils.check_k8s_cluster(viminfo):
            try:
                # wrap call to multicloud-k8s
                return k8s_infra_workload_helper.InfraWorkloadHelper.workload_detail(
                    self, vimid, workloadid, request)
            except Exception as e:
                errmsg = str(e)
                self._logger.error(errmsg)
                resp_template["workload_status_reason"] = errmsg
                return Response(data=resp_template,
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Otherwise target to openstack
        #  Get the specified tenant id
        specified_project_idorname = request.META.get("Project", None)

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
                    worker_self = openstack_infra_workload_helper.InfraWorkloadHelper(
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
                    worker_self = openstack_infra_workload_helper.InfraWorkloadHelper(
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
            self._logger.error(str(e))
            resp_template["workload_status_reason"] = str(e)
            return Response(data=resp_template,
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, vimid="", workloadid=""):
        self._logger.info("vimid, workload id: %s, %s" % (vimid, workloadid))
        self._logger.debug("META: %s" % request.META)

        resp_template = {
            "template_type": "HEAT",
            "workload_id": workloadid,
            "workload_status": "DELETE_FAILED",
            "workload_status_reason": "Exception occurs"
        }
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        # check if target to k8s
        viminfo = VimDriverUtils.get_vim_info(vimid)
        if VimDriverUtils.check_k8s_cluster(viminfo):
            try:
                # wrap call to multicloud-k8s
                return k8s_infra_workload_helper.InfraWorkloadHelper.workload_delete(
                    self, vimid, workloadid, request)
            except Exception as e:
                errmsg = str(e)
                self._logger.error(errmsg)
                resp_template["workload_status_reason"] = errmsg
                return Response(data=resp_template,
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # otherwise, target to openstack
        # Get the specified tenant id
        specified_project_idorname = request.META.get("Project", None)

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
            worker_self = openstack_infra_workload_helper.InfraWorkloadHelper(
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
            self._logger.error(str(e))
            resp_template["workload_status_reason"] = str(e)
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
