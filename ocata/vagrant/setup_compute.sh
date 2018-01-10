#!/bin/bash

set -ex

cd /opt/stack/devstack
cp /vagrant/compute.conf ./local.conf
ip=$(ip a s enp0s8 | grep inet | grep -v inet6 | sed "s/.*inet //" | cut -f1 -d'/')
sed -i "s/HOSTIP/$ip/" local.conf
su stack -c "./stack.sh"

source openrc admin admin
nova-manage cell_v2 discover_hosts
nova-manage cell_v2 map_cell_and_hosts
