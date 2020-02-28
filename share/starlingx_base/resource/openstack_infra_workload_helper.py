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
from newton_base.util import VimDriverUtils

# from newton_base.registration import registration as newton_registration
from newton_base.resource import infra_workload_helper as newton_infra_workload_helper

import yaml
NoDatesSafeLoader = yaml.SafeLoader
NoDatesSafeLoader.yaml_implicit_resolvers = {
    k: [r for r in v if r[0] != 'tag:yaml.org,2002:timestamp'] for
        k, v in list(NoDatesSafeLoader.yaml_implicit_resolvers.items())
}


logger = logging.getLogger(__name__)


# helper for infra_workload API handler targeting to openstack heat
class InfraWorkloadHelper(newton_infra_workload_helper.InfraWorkloadHelper):

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
            self._logger.error("template_update fails: %s" % str(e))

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
