#!/bin/bash
set -ex

MULTICLOUD_PLUGIN_ENDPOINT=http://172.16.77.40:9006/api/multicloud-ocata/v0/openstack-hudson-dc_RegionOne
TOKEN=$(curl -v -s -H "Content-Type: application/json" -X POST -d '{ }'  $MULTICLOUD_PLUGIN_ENDPOINT/identity/v3/auth/tokens 2>&1 | grep X-Subject-Token | sed "s/^.*: //")
#curl -v -s  -H "Content-Type: application/json" -H "X-Auth-Token: $TOKEN" -X GET $MULTICLOUD_PLUGIN_ENDPOINT/network/v2.0/networks
NETWORK_ID=$(curl -v -s -H "Content-Type: application/json" -H "X-Auth-Token: $TOKEN" -X POST -d '{"network":{ "name": "testnetwork1"}}' $MULTICLOUD_PLUGIN_ENDPOINT/network/v2.0/networks 2>/dev/null | python -mjson.tool | grep '"id"' | cut -f4 -d'"')
echo $NETWORK_ID
curl -v -s  -H "Content-Type: application/json" -H "X-Auth-Token: $TOKEN" -X GET $MULTICLOUD_PLUGIN_ENDPOINT/network/v2.0/networks/$NETWORK_ID
curl -v -s  -H "Content-Type: application/json" -H "X-Auth-Token: $TOKEN" -X HEAD $MULTICLOUD_PLUGIN_ENDPOINT/network/v2.0/networks/$NETWORK_ID
curl -v -s  -H "Content-Type: application/json" -H "X-Auth-Token: $TOKEN" -X DELETE $MULTICLOUD_PLUGIN_ENDPOINT/network/v2.0/networks/$NETWORK_ID
curl -v -s  -H "Content-Type: application/json" -H "X-Auth-Token: $TOKEN" -X GET $MULTICLOUD_PLUGIN_ENDPOINT/network/v2.0/subnets
curl -v -s  -H "Content-Type: application/json" -H "X-Auth-Token: $TOKEN" -X GET $MULTICLOUD_PLUGIN_ENDPOINT/network/v2.0/ports
curl -v -s  -H "Content-Type: application/json" -H "X-Auth-Token: $TOKEN" -X GET $MULTICLOUD_PLUGIN_ENDPOINT/network/v2.0/security-groups
curl -v -s  -H "Content-Type: application/json" -H "X-Auth-Token: $TOKEN" -X GET $MULTICLOUD_PLUGIN_ENDPOINT/network/v2.0/security-group-rules
