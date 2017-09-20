#!/bin/bash
set -ex

MULTICLOUD_PLUGIN_ENDPOINT=http://172.16.77.40:9004/api/multicloud-ocata/v0/openstack-hudson-dc_RegionOne
TOKEN=$(curl -v -s -H "Content-Type: application/json" -X POST -d '{ }'  $MULTICLOUD_PLUGIN_ENDPOINT/identity/v3/auth/tokens 2>&1 | grep X-Subject-Token | sed "s/^.*: //")
#curl -v -s  -H "Content-Type: application/json" -H "X-Auth-Token: $TOKEN" -X GET $MULTICLOUD_PLUGIN_ENDPOINT/image/v2/images
PROJECT_ID=$(curl -v -s  -H "Content-Type: application/json" -H "X-Auth-Token: $TOKEN" -X GET $MULTICLOUD_PLUGIN_ENDPOINT/identity/v3/projects 2>/dev/null | python -mjson.tool | grep -B5 "name.*\"admin" | grep '\"id\"' | cut -f4 -d'"')
curl -v -s  -H "Content-Type: application/json" -H "X-Auth-Token: $TOKEN" -X GET $MULTICLOUD_PLUGIN_ENDPOINT/identity/v3/projects/$PROJECT_ID
