#!/bin/bash

MULTICLOUD_PLUGIN_ENDPOINT=http://172.16.77.40:9004/api/multicloud-ocata/v0/openstack-hudson-dc_RegionOne
curl -v -s  -H "Content-Type: application/json" -X GET $MULTICLOUD_PLUGIN_ENDPOINT/extensions

curl -v -s  -H "Content-Type: application/json" -X GET $MULTICLOUD_PLUGIN_ENDPOINT/extensions/epa-caps
