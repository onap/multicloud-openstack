#!/bin/bash
set -ex

MULTICLOUD_PLUGIN_ENDPOINT=http://172.16.77.40:9007/api/multicloud-pike/v0/openstack-hudson-dc_RegionOne
curl -v -s  -H "Content-Type: application/json" -X GET $MULTICLOUD_PLUGIN_ENDPOINT/extensions
