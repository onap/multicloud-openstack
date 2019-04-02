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
import traceback
import uuid

from django.conf import settings
from common.exceptions import VimDriverNewtonException
# from newton_base.util import VimDriverUtils

from keystoneauth1.exceptions import HttpError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from common.msapi import extsys
from common.msapi.helper import Helper as helper

from common.utils import restcall
from newton_base.registration import registration as newton_registration
from newton_base.resource import infra_workload as newton_infra_workload
from newton_base.util import VimDriverUtils

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
        self._logger.info("data: %s" % (request.data))
        self._logger.debug("META: %s" % request.META)

        try:
            resp_template = {}
            os_status = status.HTTP_500_INTERNAL_SERVER_ERROR

            if workloadid == "":
                return super(InfraWorkload, self).post(request, vimid)
            else:
                # a post to heatbridge
                worker_self = InfraWorkloadHelper(
                    settings.MULTICLOUD_API_V1_PREFIX,
                    settings.AAI_BASE_URL
                )
                backlog_item = {
                    "id": workloadid,
                    "worker": worker_self.workload_update(),
                    "payload": (worker_self, vimid, workloadid, request.data),
                    "repeat": 0,  # one time job
                    # format of status: retcode:0 is ok, otherwise error code from http status, Status ENUM, Message
                    "status": (0, "AAI_UPDATE_IN_PROGRESS", "Pending to schedule")
                }
                gInfraWorkloadThread.add(backlog_item)
                if 0 == gInfraWorkloadThread.state():
                    gInfraWorkloadThread.start()

                # now query the progress
                backlog_item = gInfraWorkloadThread.get(workloadid)
                if not backlog_item:
                    # backlog item not found
                    return Response(
                        data={
                            'workload_status': "AAI_UPDATE_FAIL",
                            "message": "AAI update failed"
                        },
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                else:
                    progress = backlog_item.get("status", "Status not found")
                    progress_code = progress[0]
                    progress_status = progress[1]
                    progress_msg = progress[2]
                    return Response(data={'workload_status': progress_status, "message": progress_msg},
                                    status=status.HTTP_201_CREATED
                                    if progress_code == 0 else progress_code
                                    )
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, vimid="", workloadid=""):
        self._logger.info("vimid, workload id: %s, %s" % (vimid, workloadid))
        self._logger.debug("META: %s" % request.META)

        try:

            if workloadid == "":
                raise VimDriverNewtonException(
                    message="workload_id is not specified",
                    content="workload_id must be specified to delete the workload",
                    status_code = status.HTTP_400_BAD_REQUEST)

            # now query the progress
            backlog_item = gInfraWorkloadThread.get(workloadid)
            if not backlog_item:
                # backlog item not found
                return Response(
                    data={
                        'workload_status': "AAI_UPDATE_FAIL",
                        "message": "AAI update failed"
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            else:
                progress = backlog_item.get("status", "Status not found")
                progress_code = progress[0]
                progress_status = progress[1]
                progress_msg = progress[2]
                return Response(data={'workload_status': progress_status, "message": progress_msg},
                                status=status.HTTP_201_CREATED
                                if progress_code == 0 else progress_code
                                )

        except Exception as e:
            self._logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, vimid="", workloadid=""):
        self._logger.info("vimid, workload id: %s, %s" % (vimid, workloadid))
        self._logger.debug("META: %s" % request.META)

        try:

            super(InfraWorkload, self).delete(request, vimid, workloadid)

            if workloadid == "":
                raise VimDriverNewtonException(
                    message="workload_id is not specified",
                    content="workload_id must be specified to delete the workload",
                    status_code = status.HTTP_400_BAD_REQUEST)

            # a post to heatbridge delete
            worker_self = InfraWorkloadHelper(
                settings.MULTICLOUD_API_V1_PREFIX,
                settings.AAI_BASE_URL
            )
            backlog_item = {
                "id": workloadid,
                "worker": worker_self.workload_delete(),
                "payload": (worker_self, vimid, workloadid, request.data),
                "repeat": 0,  # one time job
                # format of status: retcode:0 is ok, otherwise error code from http status, Status ENUM, Message
                "status": (0, "AAI_REMOVE_IN_PROGRESS", "Pending to schedule")
            }
            gInfraWorkloadThread.add(backlog_item)
            if 0 == gInfraWorkloadThread.state():
                gInfraWorkloadThread.start()

            # now query the progress
            backlog_item = gInfraWorkloadThread.get(workloadid)
            if not backlog_item:
                # backlog item not found
                return Response(
                    data={
                        'workload_status': "STACK_REMOVE_FAILED",
                        "message": "AAI update failed"
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            else:
                progress = backlog_item.get("status", "Status not found")
                progress_code = progress[0]
                progress_status = progress[1]
                progress_msg = progress[2]
                return Response(data={'workload_status': progress_status, "message": progress_msg},
                                status=status.HTTP_200_OK
                                if progress_code == 0 else progress_code
                                )

        #     # assume the workload_type is heat
        #     stack_id = workloadid
        #     cloud_owner, regionid = extsys.decode_vim_id(vimid)
        #     # should go via multicloud proxy so that
        #     #  the selflink is updated by multicloud
        #     retcode, v2_token_resp_json, os_status = \
        #         helper.MultiCloudIdentityHelper(
        #             settings.MULTICLOUD_API_V1_PREFIX,
        #             cloud_owner, regionid, "/v2.0/tokens")
        #
        #     if retcode > 0 or not v2_token_resp_json:
        #         logger.error("authenticate fails:%s, %s, %s" %
        #                      (cloud_owner, regionid, v2_token_resp_json))
        #         return
        #     # tenant_id = v2_token_resp_json["access"]["token"]["tenant"]["id"]
        #     # tenant_name = v2_token_resp_json["access"]["token"]["tenant"]["name"]
        #
        #     # get stack status
        #     service_type = "orchestration"
        #     resource_uri = "/stacks?id=%s" % stack_id if stack_id else "/stacks"
        #     self._logger.info("retrieve stack resources, URI:%s" % resource_uri)
        #     retcode, content, os_status = \
        #         helper.MultiCloudServiceHelper(cloud_owner, regionid,
        #                                        v2_token_resp_json,
        #                                        service_type, resource_uri,
        #                                        None, "GET")
        #
        #     stacks = content.get('stacks', []) \
        #         if retcode == 0 and content else []
        #     # assume there is at most 1 stack returned
        #     #  since it was filtered by id
        #     stack1 = stacks[0] if stacks else None
        #     stack_status = ""
        #
        #     if stack1 and 'CREATE_COMPLETE' == stack1['stack_status']:
        #         # delete the stack
        #         resource_uri = "/stacks/%s/%s" % \
        #                        (stack1['stack_name'], stack1['id'])
        #         self._logger.info("delete stack, URI:%s" % resource_uri)
        #         retcode, content, os_status = \
        #             helper.MultiCloudServiceHelper(cloud_owner, regionid,
        #                                            v2_token_resp_json,
        #                                            service_type, resource_uri,
        #                                            None, "DELETE")
        #         # if retcode == 0:
        #         #    stack_status = "DELETE_IN_PROCESS"
        #         #    # and update AAI inventory by heatbridge-delete
        #         #    self.heatbridge_delete(request, vimid, stack1['id'])
        #
        #     # stub response
        #     resp_template = {
        #         "template_type": "HEAT",
        #         "workload_id": stack_id,
        #         "workload_status": stack_status
        #     }
        #
        #     if retcode > 0:
        #         resp_template["workload_response"] = content
        #
        #     self._logger.info("RESP with data> result:%s" % resp_template)
        #     return Response(status=os_status)
        # except VimDriverNewtonException as e:
        #     self._logger.error("Plugin exception> status:%s,error:%s"
        #                        % (e.status_code, e.content))
        #     return Response(data={'error': e.content}, status=e.status_code)
        # except HttpError as e:
        #     self._logger.error("HttpError: status:%s, response:%s" %
        #                        (e.http_status, e.response.json()))
        #     return Response(data=e.response.json(), status=e.http_status)
        except Exception as e:
            self._logger.error(traceback.format_exc())
            return Response(data={'error': str(e)},
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


class InfraWorkloadHelper(newton_registration.RegistryHelper):

    def __init__(self, multicloud_prefix, aai_base_url, vimid, workloadid=""):
        self.proxy_prefix = multicloud_prefix
        self.aai_base_url = aai_base_url
        self._logger = logger
        self.vimid = vimid
        self.workloadid = workloadid
        super(InfraWorkloadHelper, self).__init__()

    def workload_create(self, vimid, workload_data):
        data = workload_data
        oof_directive = data.get("oof_directives", {})
        template_type = data.get("template_type", None)
        template_data = data.get("template_data", {})
        resp_template = None
        if template_type and "heat" == template_type.lower():
            # update heat parameters from oof_directive
            parameters = template_data.get("parameters", {})

            for directive in oof_directive.get("directives", []):
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

            # update parameters
            template_data["parameters"] = parameters

            # reset to make sure "files" are empty
            template_data["files"] = {}

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
                logger.error("authenticate fails:%s,%s, %s" %
                             (cloud_owner, regionid, v2_token_resp_json))
                return (
                    retcode,
                    "authenticate fails:%s,%s, %s" %
                    (cloud_owner, regionid, v2_token_resp_json)
                )

            # tenant_id = v2_token_resp_json["access"]["token"]["tenant"]["id"]

            service_type = "orchestration"
            resource_uri = "/stacks"
            self._logger.info("retrieve stack resources, URI:%s" % resource_uri)
            retcode, content, os_status = \
                helper.MultiCloudServiceHelper(cloud_owner, regionid,
                                               v2_token_resp_json,
                                               service_type, resource_uri,
                                               template_data, "POST")

            stack1 = content.get('stack', None) \
                if retcode == 0 and content else None

            stackid = stack1["id"] if stack1 else ""
            resp_template = {
                "template_type": template_type,
                "workload_id": stackid,
                "template_response": content
            }
            self._logger.info("RESP with data> result:%s" % resp_template)
            return (0, resp_template)

    def workload_update(self, vimid, stack_id, otherinfo):
        '''
        update heat resource to AAI for the specified cloud region and tenant
        The resources includes: vserver, vserver/l-interface,
        '''

        cloud_owner, regionid = extsys.decode_vim_id(vimid)
        # should go via multicloud proxy so that the selflink is updated by multicloud
        retcode, v2_token_resp_json, os_status = \
            helper.MultiCloudIdentityHelper(settings.MULTICLOUD_API_V1_PREFIX,
                                            cloud_owner, regionid, "/v2.0/tokens")
        if retcode > 0:
            logger.error("authenticate fails:%s, %s, %s" %
                         (cloud_owner, regionid, v2_token_resp_json))

            return (retcode, "AAI_UPDATE_FAIL", "authenticate fails:%s, %s, %s" %
                         (cloud_owner, regionid, v2_token_resp_json))
        tenant_id = v2_token_resp_json["access"]["token"]["tenant"]["id"]
        # tenant_name = v2_token_resp_json["access"]["token"]["tenant"]["name"]

        # common prefix
        aai_cloud_region = \
            "/cloud-infrastructure/cloud-regions/cloud-region/%s/%s/tenants/tenant/%s" \
            % (cloud_owner, regionid, tenant_id)

        # get stack resource
        service_type = "orchestration"
        resource_uri = "/stacks/%s/resources" % (stack_id)
        self._logger.info("retrieve stack resources, URI:%s" % resource_uri)
        retcode, content, os_status = \
            helper.MultiCloudServiceHelper(cloud_owner, regionid,
                                           v2_token_resp_json,
                                           service_type, resource_uri,
                                           None, "GET")

        resources = content.get('resources', []) if retcode == 0 and content else []

        # find and update resources
        transactions = []
        for resource in resources:
            if resource.get('resource_status', None) != "CREATE_COMPLETE":
                # this resource is not ready yet
                continue
            if resource.get('resource_type', None) == 'OS::Nova::Server':
                # retrieve vserver details
                service_type = "compute"
                resource_uri = "/servers/%s" % (resource['physical_resource_id'])
                self._logger.info("retrieve vserver detail, URI:%s" % resource_uri)
                retcode, content, os_status = \
                    helper.MultiCloudServiceHelper(cloud_owner, regionid,
                                                   v2_token_resp_json,
                                                   service_type, resource_uri,
                                                   None, "GET")

                self._logger.debug(" resp data:%s" % content)
                vserver_detail = content.get('server', None) if retcode == 0 and content else None
                if vserver_detail:
                    # compose inventory entry for vserver
                    vserver_link = ""
                    for link in vserver_detail['links']:
                        if link['rel'] == 'self':
                            vserver_link = link['href']
                            break
                        pass

                    # note: relationship-list to flavor/image is not be update yet
                    # note: volumes is not updated yet
                    # note: relationship-list to vnf will be handled somewhere else
                    aai_resource = {
                        'body': {
                            'vserver-name': vserver_detail['name'],
                            'vserver-name2': vserver_detail['name'],
                            "vserver-id": vserver_detail['id'],
                            "vserver-selflink": vserver_link,
                            "prov-status": vserver_detail['status']
                        },
                        "uri": aai_cloud_region + "/vservers/vserver/%s" % (vserver_detail['id'])
                    }

                    try:
                        # then update the resource
                        retcode, content, status_code = \
                            restcall.req_to_aai(aai_resource['uri'],
                                                "PUT", content=aai_resource['body'])

                        if retcode == 0 and content:
                            content = json.JSONDecoder().decode(content)
                            self._logger.debug("AAI update %s response: %s" %
                                               (aai_resource['uri'], content))
                    except Exception:
                        self._logger.error(traceback.format_exc())
                        pass

                    aai_resource_transactions = {"put": [aai_resource]}
                    transactions.append(aai_resource_transactions)
                    # self._logger.debug("aai_resource :%s" % aai_resource_transactions)
                    pass

        for resource in resources:
            if resource.get('resource_status', None) != "CREATE_COMPLETE":
                continue
            if resource.get('resource_type', None) == 'OS::Neutron::Port':
                # retrieve vport details
                service_type = "network"
                resource_uri = "/v2.0/ports/%s" % (resource['physical_resource_id'])
                self._logger.info("retrieve vport detail, URI:%s" % resource_uri)
                retcode, content, os_status = \
                    helper.MultiCloudServiceHelper(cloud_owner, regionid,
                                                   v2_token_resp_json,
                                                   service_type, resource_uri,
                                                   None, "GET")

                self._logger.debug(" resp data:%s" % content)

                vport_detail = content.get('port', None) if retcode == 0 and content else None
                if vport_detail:
                    # compose inventory entry for vport
                    # note: l3-interface-ipv4-address-list,
                    #  l3-interface-ipv6-address-list are not updated yet
                    # note: network-name is not update yet since the detail
                    #  coming with network-id
                    aai_resource = {
                        "body": {
                            "interface-name": vport_detail['name'],
                            "interface-id": vport_detail['id'],
                            "macaddr": vport_detail['mac_address']
                        },
                        'uri':
                            aai_cloud_region + "/vservers/vserver/%s/l-interfaces/l-interface/%s"
                                               % (vport_detail['device_id'], vport_detail['name'])
                    }
                    try:
                        # then update the resource
                        retcode, content, status_code = \
                            restcall.req_to_aai(aai_resource['uri'], "PUT",
                                                content=aai_resource['body'])

                        if retcode == 0 and content:
                            content = json.JSONDecoder().decode(content)
                            self._logger.debug("AAI update %s response: %s" %
                                               (aai_resource['uri'], content))
                    except Exception:
                        self._logger.error(traceback.format_exc())
                        pass

                    aai_resource_transactions = {"put": [aai_resource]}
                    transactions.append(aai_resource_transactions)
                    # self._logger.debug("aai_resource :%s" % aai_resource_transactions)

                    pass

        # aai_transactions = {"transactions": transactions}
        # self._logger.debug("aai_transactions :%s" % aai_transactions)
        return (retcode, "AAI_UPDATE_COMPLETE", "succeed")

    def workload_delete(self, vimid, stack_id, otherinfo):
        '''
        remove heat resource from AAI for the specified cloud region and tenant

        '''

        # enumerate the resources
        cloud_owner, regionid = extsys.decode_vim_id(vimid)
        # should go via multicloud proxy so that the selflink is updated by multicloud
        retcode, v2_token_resp_json, os_status = \
            helper.MultiCloudIdentityHelper(settings.MULTICLOUD_API_V1_PREFIX,
                                            cloud_owner, regionid, "/v2.0/tokens")
        if retcode > 0:
            logger.error("authenticate fails:%s, %s, %s" %
                         (cloud_owner, regionid, v2_token_resp_json))
            return None

        tenant_id = v2_token_resp_json["access"]["token"]["tenant"]["id"]
        # tenant_name = v2_token_resp_json["access"]["token"]["tenant"]["name"]

        # common prefix
        aai_cloud_region = \
            "/cloud-infrastructure/cloud-regions/cloud-region/%s/%s/tenants/tenant/%s" \
            % (cloud_owner, regionid, tenant_id)

        # get stack resource
        service_type = "orchestration"
        resource_uri = "/stacks/%s/resources" % (stack_id)
        self._logger.info("retrieve stack resources, URI:%s" % resource_uri)
        retcode, content, os_status = \
            helper.MultiCloudServiceHelper(cloud_owner, regionid,
                                           v2_token_resp_json,
                                           service_type, resource_uri,
                                           None, "GET")
        resources = content.get('resources', []) \
            if retcode == 0 and content else []

        vserver_list = [resource['physical_resource_id'] for resource in resources
                        if resource.get('resource_type', None) == 'OS::Nova::Server']

        try:
            # get list of vservers
            vserver_list_url = aai_cloud_region + "/vservers?depth=all"
            retcode, content, status_code = \
                restcall.req_to_aai(vserver_list_url, "GET")
            if retcode > 0 or not content:
                self._logger.debug("AAI get %s response: %s" % (vserver_list_url, content))
                return (retcode, "AAI_REMOVE_FAIL", "authenticate fails:%s, %s, %s" %
                        (cloud_owner, regionid, v2_token_resp_json))

            content = json.JSONDecoder().decode(content)
            vservers = content['vserver']
            for vserver in vservers:
                if vserver['vserver-id'] not in vserver_list:
                    continue

                try:
                    # iterate vport, except will be raised if no l-interface exist
                    for vport in vserver['l-interfaces']['l-interface']:
                        # delete vport
                        vport_delete_url = \
                            aai_cloud_region + \
                            "/vservers/vserver/%s/l-interfaces/l-interface/%s?resource-version=%s" \
                            % (vserver['vserver-id'], vport['interface-name'],
                               vport['resource-version'])

                        restcall.req_to_aai(vport_delete_url, "DELETE")
                except Exception:
                    pass

                try:
                    # delete vserver
                    vserver_delete_url = \
                        aai_cloud_region + \
                        "/vservers/vserver/%s?resource-version=%s" \
                        % (vserver['vserver-id'], vserver['resource-version'])

                    restcall.req_to_aai(vserver_delete_url, "DELETE")
                except Exception:
                    continue

            return (retcode, "AAI_REMOVE_COMPLETE", "succeed")
        except Exception:
            self._logger.error(traceback.format_exc())
            return None
        pass
