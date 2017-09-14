#!/bin/bash
export MULTICLOUD_PLUGIN_ENDPOINT=http://172.16.77.40:9004/api/multicloud-ocata/v0/openstack-hudson-dc_RegionOne
curl -v -s -H "Content-Type: application/json" -H "X-Auth-Token: $TOKEN" -X GET http://172.16.77.40:9004/api/multicloud-ocata/v0/swagger.json
curl -v -s -H "Content-Type: application/json" -X POST -d '{ }'  $MULTICLOUD_PLUGIN_ENDPOINT/identity/v3/auth/tokens | grep X-Subject-Token
