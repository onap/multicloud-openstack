# Copyright (c) 2017-2020 Wind River Systems, Inc.
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
import json
import requests
import tarfile
import base64
from ruamel import yaml


from rest_framework import status
from rest_framework.response import Response

from django.conf import settings
from common.msapi import extsys
from newton_base.util import VimDriverUtils

logger = logging.getLogger(__name__)


# wrap calls to multicloud-k8s infra_workload API
class InfraWorkloadHelper:

    # def resettarfile(tarinfo):
    #     tarinfo.uid = tarinfo.gid = 0
    #     tarinfo.uname = tarinfo.gname = "root"
    #     return tarinfo

    def workload_create(self, vimid, workloadid, request):
        '''
        Deploy workload to target k8s via multicloud-k8s
        :param vimid:
        :param workloadid:
        :param request
        '''
        # resp_template = {
        #     "template_type": "HEAT",
        #     "workload_id": workloadid,
        #     "workload_status": "GET_FAILED",
        #     "workload_status_reason": "Exception occurs"
        # }
        # status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        # viminfo = VimDriverUtils.get_vim_info(vimid)
        workload_query = VimDriverUtils.get_query_part(request)
        workload_data = request.data

        # vf_module_model_customization_id = data.get("vf-module-model-customization-id", None)
        # vf_module_id = data.get("vf-module-id", "")
        user_directive = workload_data.get("user_directives", {})
        # oof_directive = data.get("oof_directives", {})
        # sdnc_directive = data.get("sdnc_directives", {})
        # template_type = data.get("template_type")
        # template_data = data.get("template_data", {})

        # 1, create profile if not exists
        # manifest.yaml content
        manifest_yaml_json = {
            "version": "v1",
            "type": {
                "values": "override_values.yaml"
            }
        }

        # override_values.yaml content
        override_values_yaml_json = ""

        # extract rb and profile info from user_directive
        rbname = None
        rbversion = None
        profilename = None

        for attr in user_directive.get("attributes", []):
            aname = attr.get("attribute_name", None)
            avalue = attr.get("attribute_value", None)
            if aname == "override_values_yaml_base64":
                override_values_yaml_json = yaml.load(base64.b64decode(avalue), Loader=yaml.Loader)
            elif aname == "definition-name":
                rbname = avalue
            elif aname == "definition-version":
                rbversion = avalue
            elif aname == "profile-name":
                profilename = avalue

        multicloudK8sUrl = "%s://%s:%s/api/multicloud-k8s/v1" % (
            settings.MSB_SERVICE_PROTOCOL, settings.MSB_SERVICE_ADDR, settings.MSB_SERVICE_PORT)
        if rbname and rbversion and profilename and override_values_yaml_json:
            # package them into tarball
            basedir="/tmp/%s_%s_%s/" % (rbname, rbversion, profilename)
            manifest_yaml_filename="manifest.yaml"
            override_values_yaml_filename = "override_values.yaml"
            profile_filename = "profile.tar.gz"
            if not os.path.isdir(basedir):
                os.mkdir(basedir)
            logger.debug("k8s profile temp dir for %s,%s,%s is %s" % (rbname, rbversion, profilename, basedir))
            with open(basedir+manifest_yaml_filename, "w") as f_manifest_yaml:
                yaml.dump(manifest_yaml_json, f_manifest_yaml, Dumper=yaml.RoundTripDumper)
            with open(basedir+override_values_yaml_filename, "w") as f_override_values_yaml:
                yaml.dump(override_values_yaml_json, f_override_values_yaml, Dumper=yaml.RoundTripDumper)

            tar = tarfile.open(basedir+profile_filename, "w:gz")
            # tar.add(basedir+manifest_yaml_filename, arcname=manifest_yaml_filename,filter=resettarfile)
            tar.add(basedir+manifest_yaml_filename, arcname=manifest_yaml_filename)
            tar.add(basedir+override_values_yaml_filename, arcname=override_values_yaml_filename)
            tar.close()

            # create profile and upload content
            create_rbprofile_json = {
                "rb-name": rbname,
                "rb-version": rbversion,
                "profile-name": profilename,
                "release-name": "r1",
                "namespace": "testnamespace1",
                "kubernetes-version": "1.16.2"
            }

            profileUrl = multicloudK8sUrl+"/v1/rb/definition/%s/%s/profile" % (rbname, rbversion)

            #data = open('create_rbprofile.json')
            response = requests.post(profileUrl, data=json.dumps(create_rbprofile_json), verify=False)
            logger.debug("create profile, returns: %s,%s" % (response.content, response.status_code))

            profileContentUrl = profileUrl + "/%s/content" % (profilename)
            #profileContent = open(basedir+profile_filename, 'rb').read()
            with open(basedir+profile_filename, "rb") as profileContent:
                response = requests.post(profileContentUrl, data=profileContent.read(), verify=False)
                logger.debug("upload profile content, returns: %s,%s" % (response.content, response.status_code))

        # 2.forward infra_workload API requests with queries
        cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)
        infraUrl = multicloudK8sUrl+"/%s/%s/infra_workload" % (cloud_owner, cloud_region_id)
        if workloadid:
            infraUrl += ("/%s" % workloadid)
        if workload_query:
            infraUrl += ("?%s" % workload_query)

        # should we forward headers ? TBD
        logger.debug("request with url,content: %s,%s" % (infraUrl, workload_data))
        resp = requests.post(infraUrl, data=json.dumps(workload_data), verify=False)
        # resp_template["workload_status_reason"] = resp.content
        logger.debug("response status,content: %s,%s" % (resp.status_code, resp.content))
        return Response(data=json.loads(resp.content), status=resp.status_code)


    def workload_delete(self, vimid, workloadid, request):
        '''
        remove workload
        '''
        # resp_template = {
        #     "template_type": "HEAT",
        #     "workload_id": workloadid,
        #     "workload_status": "GET_FAILED",
        #     "workload_status_reason": "Exception occurs"
        # }
        # status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        workload_query_str = VimDriverUtils.get_query_part(request)
        workload_data = request.data
        
        multicloudK8sUrl = "%s://%s:%s/api/multicloud-k8s/v1" % (
            settings.MSB_SERVICE_PROTOCOL, settings.MSB_SERVICE_ADDR, settings.MSB_SERVICE_PORT)

        # 1.forward infra_workload API requests with queries
        cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)
        infraUrl = multicloudK8sUrl+"/%s/%s/infra_workload" % (cloud_owner, cloud_region_id)
        if workloadid:
            infraUrl += ("/%s" % workloadid)
        if workload_query_str:
            infraUrl += ("?%s" % workload_query_str)

        # should we forward headers ? TBD
        logger.debug("request with url,content: %s,%s" % (infraUrl, workload_data))
        resp = requests.delete(infraUrl, data=json.dumps(workload_data), verify=False)
        # resp_template["workload_status_reason"] = resp.content
        logger.debug("response status,content: %s,%s" % (resp.status_code, resp.content))
        return Response(data=json.loads(resp.content), status=resp.status_code)


    def workload_detail(self, vimid, workloadid, request):
        '''
        get workload status
        '''
        # resp_template = {
        #     "template_type": "HEAT",
        #     "workload_id": workloadid,
        #     "workload_status": "GET_FAILED",
        #     "workload_status_reason": "Exception occurs"
        # }
        # status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        workload_query_str = VimDriverUtils.get_query_part(request)
        workload_data = request.data
        
        multicloudK8sUrl = "%s://%s:%s/api/multicloud-k8s/v1" % (
            settings.MSB_SERVICE_PROTOCOL, settings.MSB_SERVICE_ADDR, settings.MSB_SERVICE_PORT)

        # forward infra_workload API requests with queries
        cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)
        infraUrl = multicloudK8sUrl+"/%s/%s/infra_workload" % (cloud_owner, cloud_region_id)
        if workloadid:
            infraUrl += ("/%s" % workloadid)
        if workload_query_str:
            infraUrl += ("?%s" % workload_query_str)

        # should we forward headers ? TBD
        logger.debug("request with url,content: %s,%s" % (infraUrl, workload_data))
        resp = requests.get(infraUrl, data=json.dumps(workload_data), verify=False)
        # resp_template["workload_status_reason"] = resp.content
        logger.debug("response status,content: %s,%s" % (resp.status_code, resp.content))
        return Response(data=json.loads(resp.content), status=resp.status_code)
