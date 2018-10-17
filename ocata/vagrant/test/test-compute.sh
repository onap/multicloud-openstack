#!/bin/bash
# Copyright (c) 2018 Intel Corporation.
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

set -ex

MULTICLOUD_PLUGIN_ENDPOINT=http://172.16.77.40:9006/api/multicloud-ocata/v0/openstack-hudson-dc_RegionOne
TOKEN=$(curl -v -s -H "Content-Type: application/json" -X POST -d '{ }'  $MULTICLOUD_PLUGIN_ENDPOINT/identity/v3/auth/tokens 2>&1 | grep X-Subject-Token | sed "s/\r//g" | sed "s/^.*: //" |  cat -v)
PROJECT_ID=$(curl -v -s  -H "Content-Type: application/json" -H "X-Auth-Token: $TOKEN" -X GET $MULTICLOUD_PLUGIN_ENDPOINT/identity/v3/projects 2>/dev/null | python -mjson.tool | grep -B5 "name.*\"admin" | grep '\"id\"' | cut -f4 -d'"')
curl -v -s  -H "Content-Type: application/json" -H "X-Auth-Token: $TOKEN" -X GET $MULTICLOUD_PLUGIN_ENDPOINT/compute/v2.1/$PROJECT_ID/os-hypervisors
curl -v -s  -H "Content-Type: application/json" -H "X-Auth-Token: $TOKEN" -X GET $MULTICLOUD_PLUGIN_ENDPOINT/compute/v2.1/$PROJECT_ID/os-hypervisors/detail
curl -v -s  -H "Content-Type: application/json" -H "X-Auth-Token: $TOKEN" -X GET $MULTICLOUD_PLUGIN_ENDPOINT/identity/v3/projects/$PROJECT_ID
curl -v -s  -H "Content-Type: application/json" -H "X-Auth-Token: $TOKEN" -X GET $MULTICLOUD_PLUGIN_ENDPOINT/compute/v2.1/$PROJECT_ID/flavors
curl -v -s  -H "Content-Type: application/json" -H "X-Auth-Token: $TOKEN" -X GET $MULTICLOUD_PLUGIN_ENDPOINT/compute/v2.1/$PROJECT_ID/flavors/1
curl -v -s  -H "Content-Type: application/json" -H "X-Auth-Token: $TOKEN" -X DELETE $MULTICLOUD_PLUGIN_ENDPOINT/compute/v2.1/$PROJECT_ID/flavors/93 || true
curl -v -s  -H "Content-Type: application/json" -H "X-Auth-Token: $TOKEN" -X POST -d '{"flavor":{"id":"93","vcpus": 4,"name": "test222", "ram":4096, "os-flavor-access:is_public":true,"disk":10 , "swap":1024, "OS-FLV-EXT-DATA:ephemeral":0 }}' $MULTICLOUD_PLUGIN_ENDPOINT/compute/v2.1/$PROJECT_ID/flavors
curl -v -s  -H "Content-Type: application/json" -H "X-Auth-Token: $TOKEN" -X GET $MULTICLOUD_PLUGIN_ENDPOINT/compute/v2.1/$PROJECT_ID/flavors/93
curl -v -s  -H "Content-Type: application/json" -H "X-Auth-Token: $TOKEN" -X DELETE $MULTICLOUD_PLUGIN_ENDPOINT/compute/v2.1/$PROJECT_ID/flavors/93
curl -v -s  -H "Content-Type: application/json" -H "X-Auth-Token: $TOKEN" -X GET $MULTICLOUD_PLUGIN_ENDPOINT/compute/v2.1/$PROJECT_ID/servers
