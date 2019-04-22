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
from rest_framework import status
from django.conf import settings
from common.msapi import extsys
from common.msapi.helper import Helper as helper

from common.utils import restcall
from newton_base.registration import registration as newton_registration

logger = logging.getLogger(__name__)


class InfraWorkloadHelper(object):

    def __init__(self, multicloud_prefix, aai_base_url):
        self.proxy_prefix = multicloud_prefix
        self.aai_base_url = aai_base_url
        self._logger = logger
        super(InfraWorkloadHelper, self).__init__()

    def workload_create(self, vimid, workload_data, project_idorname=None):
        '''
        Instantiate a stack over target cloud region (OpenStack instance)
        :param vimid:
        :param workload_data:
        :param project_idorname
        :return: result code, status enum, status reason
            result code: 0-ok, otherwise error
            status enum: "CREATE_IN_PROGRESS", "CREATE_FAILED"
            status reason: message to explain the status enum
        '''
        data = workload_data
        oof_directive = data.get("oof_directives", {})
        template_type = data.get("template_type", None)
        template_data = data.get("template_data", {})
        # resp_template = None
        if not template_type or "heat" != template_type.lower():
            return status.HTTP_400_BAD_REQUEST, "CREATE_FAILED", \
                   "Bad parameters: template type %s is not heat" %\
                   template_type or ""

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
            self._logger.info("workload_create fail: %s" % content)
            return os_status, "CREATE_FAILED", content

    def workload_update(self, vimid, stack_id, otherinfo=None, project_idorname=None):
        '''
        update heat resource to AAI for the specified cloud region and tenant
        The resources includes: vserver, vserver/l-interface,
        :param vimid:
        :param stack_id: id of the created stack in OpenStack instance
        :param stack_name: name of stack
        :param otherinfo:
        :return: result code, status enum, status reason
            result code: 0-ok, otherwise error
            status enum: "UPDATE_IN_PROGRESS", "UPDATE_FAILED"
            status reason: message to explain the status enum
        '''

        cloud_owner, regionid = extsys.decode_vim_id(vimid)
        # should go via multicloud proxy so that the selflink is updated by multicloud
        retcode, v2_token_resp_json, os_status = \
            helper.MultiCloudIdentityHelper(
                settings.MULTICLOUD_API_V1_PREFIX,
                cloud_owner, regionid, "/v2.0/tokens",
                {"Project": project_idorname})
        if retcode > 0:
            errmsg = "authenticate fails:%s, %s, %s" %\
                     (cloud_owner, regionid, v2_token_resp_json)
            logger.error(errmsg)
            return os_status, "UPDATE_FAILED", errmsg

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
        if retcode > 0:
            errmsg = "stack:%s, query fails: %s" %\
                     (resource_uri, content)
            logger.error(errmsg)
            return os_status, "UPDATE_FAILED", content

        # find and update resources
        # transactions = []
        for resource in resources:
            if resource.get('resource_status', None) != "CREATE_COMPLETE":
                # this resource is not ready yet, just return
                errmsg = "stack: %s, resource not ready :%s" % \
                         (resource_uri, resource)
                logger.info(errmsg)
                return status.HTTP_206_PARTIAL_CONTENT, "UPDATE_FAILED", errmsg
                # continue
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
                if retcode > 0:
                    errmsg = "stack resource:%s, query fails: %s" % \
                             (resource_uri, content)
                    logger.error(errmsg)
                    return os_status, "UPDATE_FAILED", content
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
                    except Exception as e:
                        self._logger.error(e.message)
                        return status.HTTP_500_INTERNAL_SERVER_ERROR, "UPDATE_FAILED", e.message

                    # aai_resource_transactions = {"put": [aai_resource]}
                    # transactions.append(aai_resource_transactions)
                    # self._logger.debug("aai_resource :%s" % aai_resource_transactions)

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
                if retcode > 0:
                    errmsg = "stack resource:%s, query fails: %s" % \
                             (resource_uri, content)
                    logger.error(errmsg)
                    return os_status, "UPDATE_FAILED", content

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
                    except Exception as e:
                        self._logger.error(e.message)
                        return status.HTTP_500_INTERNAL_SERVER_ERROR, "UPDATE_FAILED", e.message

                    # aai_resource_transactions = {"put": [aai_resource]}
                    # transactions.append(aai_resource_transactions)
                    # self._logger.debug("aai_resource :%s" % aai_resource_transactions)

        # aai_transactions = {"transactions": transactions}
        # self._logger.debug("aai_transactions :%s" % aai_transactions)
        return 0, "UPDATE_COMPLETE", "succeed"

    def workload_delete(self, vimid, stack_id, otherinfo=None, project_idorname=None):
        '''
        remove heat resource from AAI for the specified cloud region and tenant
        The resources includes: vserver, vserver/l-interface,
        :param vimid:
        :param stack_id: id of the created stack in OpenStack instance
        :param otherinfo:
        :return: result code, status enum, status reason
            result code: 0-ok, otherwise error
            status enum: "DELETE_IN_PROGRESS", "DELETE_FAILED"
            status reason: message to explain the status enum
        '''

        # enumerate the resources
        cloud_owner, regionid = extsys.decode_vim_id(vimid)
        # should go via multicloud proxy so that the selflink is updated by multicloud
        retcode, v2_token_resp_json, os_status = \
            helper.MultiCloudIdentityHelper(
                settings.MULTICLOUD_API_V1_PREFIX,
                cloud_owner, regionid, "/v2.0/tokens",
                {"Project": project_idorname})
        if retcode > 0:
            errmsg = "authenticate fails:%s, %s, %s" %\
                     (cloud_owner, regionid, v2_token_resp_json)
            logger.error(errmsg)
            return os_status, "DELETE_FAILED", errmsg

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
                return (status_code, "DELETE_FAILED", "authenticate fails:%s, %s, %s" %
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
                except Exception as e:
                    # return 12, "DELETE_FAILED", e.message
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

            return 0, "DELETE_COMPLETE", "succeed"
        except Exception as e:
            self._logger.error(e.message)
            return status.HTTP_500_INTERNAL_SERVER_ERROR, "DELETE_FAILED", e.message
        pass

    def workload_status(self, vimid, stack_id=None, stack_name=None, otherinfo=None, project_idorname=None):
        '''
        get workload status by either stack id or name
        :param vimid:
        :param stack_id:
        :param stack_name:
        :param otherinfo:
        :return:
        '''
        try:
            # assume the workload_type is heat
            cloud_owner, regionid = extsys.decode_vim_id(vimid)
            # should go via multicloud proxy so that the selflink is updated by multicloud
            retcode, v2_token_resp_json, os_status = \
                helper.MultiCloudIdentityHelper(
                    settings.MULTICLOUD_API_V1_PREFIX,
                    cloud_owner, regionid, "/v2.0/tokens",
                {"Project": project_idorname})

            if retcode > 0 or not v2_token_resp_json:
                errmsg = "authenticate fails:%s, %s, %s" % \
                         (cloud_owner, regionid, v2_token_resp_json)
                logger.error(errmsg)
                return os_status, "GET_FAILED", errmsg

            # get stack status
            service_type = "orchestration"
            resource_uri = "/stacks"
            if stack_id:
                resource_uri = "/stacks?id=%s" % stack_id
            elif stack_name:
                resource_uri = "/stacks?name=%s" % stack_name

            self._logger.info("retrieve stack resources, URI:%s" % resource_uri)
            retcode, content, os_status = \
                helper.MultiCloudServiceHelper(cloud_owner, regionid,
                                               v2_token_resp_json,
                                               service_type, resource_uri,
                                               None, "GET")

            if retcode > 0 or not content:
                errmsg = "Stack query %s response: %s" % (resource_uri, content)
                self._logger.debug(errmsg)
                return os_status, "GET_FAILED", content

            stacks = content.get('stacks', [])  # if retcode == 0 and content else []
            # stack_status = stacks[0].get("stack_status", "GET_FAILED") if len(stacks) > 0 else "GET_FAILED"
            workload_status = "GET_COMPLETE"

            return retcode, workload_status, content
        except Exception as e:
            self._logger.error(e.message)
            return status.HTTP_500_INTERNAL_SERVER_ERROR, "GET_FAILED", e.message


    def workload_detail(self, vimid, stack_id, nexturi=None, otherinfo=None, project_idorname=None):
        '''
        get workload status by either stack id or name
        :param vimid:
        :param stack_id:
        :param nexturi: stacks/<stack id>/<nexturi>
        :param otherinfo:
        :return:
        '''
        try:
            # assume the workload_type is heat
            cloud_owner, regionid = extsys.decode_vim_id(vimid)
            # should go via multicloud proxy so that the selflink is updated by multicloud
            retcode, v2_token_resp_json, os_status = \
                helper.MultiCloudIdentityHelper(
                    settings.MULTICLOUD_API_V1_PREFIX,
                    cloud_owner, regionid, "/v2.0/tokens",
                {"Project": project_idorname})

            if retcode > 0 or not v2_token_resp_json:
                errmsg = "authenticate fails:%s, %s, %s" % \
                         (cloud_owner, regionid, v2_token_resp_json)
                logger.error(errmsg)
                return os_status, "GET_FAILED", errmsg

            # get stack status
            service_type = "orchestration"
            resource_uri = "/stacks/%s" % stack_id
            if nexturi:
                resource_uri += "/" + nexturi

            self._logger.info("retrieve stack resources, URI:%s" % resource_uri)
            retcode, content, os_status = \
                helper.MultiCloudServiceHelper(cloud_owner, regionid,
                                               v2_token_resp_json,
                                               service_type, resource_uri,
                                               None, "GET")

            if retcode > 0 or not content:
                errmsg = "Stack query %s response: %s" % (resource_uri, content)
                self._logger.debug(errmsg)
                return os_status, "GET_FAILED", content

            stack = content.get('stack', {})  # if retcode == 0 and content else []
            workload_status = stack.get("stack_status", "GET_FAILED")
            # workload_status = "GET_COMPLETE"

            return 0, workload_status, content
        except Exception as e:
            self._logger.error(e.message)
            return status.HTTP_500_INTERNAL_SERVER_ERROR, "GET_FAILED", e.message
