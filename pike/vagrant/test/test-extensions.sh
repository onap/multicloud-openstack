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

MULTICLOUD_PLUGIN_ENDPOINT=http://172.16.77.40:9007/api/multicloud-pike/v0/openstack-hudson-dc_RegionOne
curl -v -s  -H "Content-Type: application/json" -X GET $MULTICLOUD_PLUGIN_ENDPOINT/extensions
