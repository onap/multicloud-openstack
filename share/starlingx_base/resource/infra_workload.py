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
from django.conf import settings

from rest_framework import status
from rest_framework.response import Response
from common.msapi import extsys
from common.msapi.helper import Helper as helper

from newton_base.resource import infra_workload as newton_infra_workload
from newton_base.resource import infra_workload_helper as infra_workload_helper

logger = logging.getLogger(__name__)

# global var: Audition thread
# the id is the workloadid, which implies post to workloadid1 followed by delete workloadid1
# will replace the previous backlog item
gInfraWorkloadThread = helper.MultiCloudThreadHelper()

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

        try:
            worker_self = infra_workload_helper.InfraWorkloadHelper(
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
                    progress_code = progress[0]
                    progress_status = progress[1]
                    progress_msg = progress[2]
                    resp_template["workload_status"] = progress_status
                    resp_template["workload_status_reason"] = progress_msg
                    return Response(data=resp_template,
                                    status=status.HTTP_200_ACCEPTED
                                    if progress_code == 0 else progress_code
                                    )
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
        try:

            if workloadid == "":
                resp_template["workload_status_reason"] = "workload id is not found in API url"
                return Response(
                    data=resp_template,
                    status=status.HTTP_400_BAD_REQUEST
                )

            # now query the progress
            status_code = status.HTTP_200_OK
            backlog_item = gInfraWorkloadThread.get(workloadid)
            if not backlog_item:
                # backlog item not found, so check the stack status
                worker_self = infra_workload_helper.InfraWorkloadHelper(
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
                progress_code = progress[0]
                progress_status = progress[1]
                progress_msg = progress[2]
                # if gInfraWorkloadThread.expired(workloadid):
                #     gInfraWorkloadThread.remove(workloadid)
                resp_template["workload_status"] = progress_status
                resp_template["workload_status_reason"] = progress_msg
                status_code = status.HTTP_200_OK\
                    if progress_code == 0 else progress_code

            return Response(data=resp_template,
                            status=status_code
                            )

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
            worker_self = infra_workload_helper.InfraWorkloadHelper(
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
                progress_code = progress[0]
                progress_status = progress[1]
                progress_msg = progress[2]
                # if gInfraWorkloadThread.expired(workloadid):
                #     gInfraWorkloadThread.remove(workloadid)

                resp_template["workload_status"] = progress_status
                resp_template["workload_status_reason"] = progress_msg
                return Response(data=resp_template,
                                status=status.HTTP_204_NO_CONTENT
                                if progress_code == 0 else progress_code
                                )
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

