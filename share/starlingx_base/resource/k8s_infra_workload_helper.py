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
import requests
import tarfile

from django.conf import settings
from common.msapi import extsys
from newton_base.util import VimDriverUtils

logger = logging.getLogger(__name__)


# wrap calls to multicloud-k8s infra_workload API
class InfraWorkloadHelper:

    # def __init__(self, multicloud_prefix, aai_base_url):
    #     self.proxy_prefix = multicloud_prefix
    #     self.aai_base_url = aai_base_url
    #     self._logger = logger
    #     super(InfraWorkloadHelper, self).__init__(multicloud_prefix, aai_base_url)


    # def resettarfile(tarinfo):
    #     tarinfo.uid = tarinfo.gid = 0
    #     tarinfo.uname = tarinfo.gname = "root"
    #     return tarinfo

    @staticmethod
    def workload_create(self, vimid, workloadid, request):
        '''
        Deploy workload to target k8s via multicloud-k8s
        :param vimid:
        :param workloadid:
        :param request
        '''

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
        manifest_yaml = {
            "version": "v1",
            "type": {
                "values": "override_values.yaml"
            }
        }

        # override_values.yaml content
        override_values_yaml = ""

        # extract rb and profile info from user_directive
        rbname = "fakerbname"
        rbversion = "1"
        profilename = "p1"

        for attr in user_directive.get("attributes", []):
            aname = attr.get("attribute_name", None)
            avalue = attr.get("attribute_value", None)
            if aname == "override_values":
                # manifest_yaml = avalue["manifest_yaml"]
                # #override_values_yaml = avalue["override_values_yaml"]
                override_values_yaml = avalue
            elif aname == "definition-name":
                rbname = avalue
            elif aname == "definition-version":
                rbversion = avalue
            elif aname == "profile-name":
                profilename = avalue

        # package them into tarball
        basedir="/tmp/%s_%s_%s/" % (rbname, rbversion, profilename)
        manifest_yaml_filename="manifest.yaml"
        override_values_yaml_filename = "override_values.yaml"
        profile_filename = "profile.tar.gz"
        if not os.path.isdir(basedir):
            os.mkdir(basedir)
        self._logger.debug("k8s profile temp dir for %s,%s,%s is %s" % (rbname, rbversion, profilename, basedir))
        with open(basedir+manifest_yaml_filename, "w") as f:
            yaml.dump(manifest_yaml, f, Dumper=yaml.RoundTripDumper)
        with open(basedir+override_values_yaml_filename, "w") as f:
            #yaml.dump(override_values_yaml, f, Dumper=yaml.RoundTripDumper)
            f.write(override_values_yaml)

        tar = tarfile.open(basedir+profile_filename, "w:gz")
        # tar.add(basedir+manifest_yaml_filename, arcname=manifest_yaml_filename,filter=resettarfile)
        tar.add(basedir+manifest_yaml_filename, arcname=manifest_yaml_filename)
        tar.add(basedir+override_values_yaml_filename, arcname=override_values_yaml_filename, filter=reset)
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

        multicloudK8sUrl = "%s://%s:%s/api/multicloud-k8s/v1" % (
            settings.MSB_SERVICE_PROTOCOL, settings.MSB_SERVICE_ADDR, settings.MSB_SERVICE_PORT)
        profileUrl = multicloudK8sUrl+"/v1/rb/definition/%s/%s/profile" % (rbname, rbversion)

        #data = open('create_rbprofile.json')
        response = requests.post(profileUrl, data=json.dumps(create_rbprofile_json), verify=False)
        self._logger.debug("create profile, returns: %s,%s" % (response.content, response.status_code))

        profileContentUrl = profileUrl + "/%s/content" % (profilename)
        #profileContent = open(basedir+profile_filename, 'rb').read()
        with open(basedir+override_values_yaml_filename, "rb") as profileContent:
            response = requests.post(profileContentUrl, data=profileContent.read(), verify=False)
        self._logger.debug("upload profile content, returns: %s,%s" % (response.content, response.status_code))

        # 2.forward infra_workload API requests with queries
        cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)
        infraUrl = multicloudK8sUrl+"/%s/%s/infra_workload?%s" % (cloud_owner, cloud_region_id)
        if workload_query:
            infraUrl += ("?%s" % workload_query)

        # should we forward headers ? TBD
        return requests.post(infraUrl, data=workload_data, verify=False)


    @staticmethod
    def workload_delete(self, vimid, workloadid, request):
        '''
        remove workload
        '''
        workload_query_str = VimDriverUtils.get_query_part(request)
        workload_data = request.data
        
        multicloudK8sUrl = "%s://%s:%s/api/multicloud-k8s/v1" % (
            settings.MSB_SERVICE_PROTOCOL, settings.MSB_SERVICE_ADDR, settings.MSB_SERVICE_PORT)

        # 1.forward infra_workload API requests with queries
        cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)
        infraUrl = multicloudK8sUrl+"/%s/%s/infra_workload" % (cloud_owner, cloud_region_id)
        if workload_query_str:
            infraUrl += ("?%s" % workload_query_str)

        # should we forward headers ? TBD
        return requests.delete(infraUrl, data=workload_data, verify=False)


    @staticmethod
    def workload_detail(self, vimid, workloadid, request):
        '''
        get workload status
        '''

        workload_query_str = VimDriverUtils.get_query_part(request)
        workload_data = request.data
        
        multicloudK8sUrl = "%s://%s:%s/api/multicloud-k8s/v1" % (
            settings.MSB_SERVICE_PROTOCOL, settings.MSB_SERVICE_ADDR, settings.MSB_SERVICE_PORT)

        # 1.forward infra_workload API requests with queries
        cloud_owner, cloud_region_id = extsys.decode_vim_id(vimid)
        infraUrl = multicloudK8sUrl+"/%s/%s/infra_workload" % (cloud_owner, cloud_region_id)
        if workload_query_str:
            infraUrl += ("?%s" % workload_query_str)

        # should we forward headers ? TBD
        return requests.get(infraUrl, data=workload_data, verify=False)
