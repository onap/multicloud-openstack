#!/bin/bash
set -ex

MULTICLOUD_PLUGIN_ENDPOINT=http://172.16.77.40:9006/api/multicloud-ocata/v0/openstack-hudson-dc_RegionOne
TOKEN=$(curl -v -s -H "Content-Type: application/json" -X POST -d '{ }'  $MULTICLOUD_PLUGIN_ENDPOINT/identity/v3/auth/tokens 2>&1 | grep X-Subject-Token | sed "s/^.*: //")
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
