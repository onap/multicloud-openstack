#!/bin/bash

set -ex

cd /opt/stack/devstack
cp /vagrant/compute.conf ./local.conf
data_if=$(ifconfig | grep 192.168.* -B 1 | awk -F " " 'NR==1{print $1}')
ip=$(ip a s $data_if | grep inet | grep -v inet6 | sed "s/.*inet //" | cut -f1 -d'/')
sed -i "s/HOSTIP/$ip/" local.conf
su stack -c "./stack.sh"

source openrc admin admin
nova-manage cell_v2 discover_hosts
nova-manage cell_v2 map_cell_and_hosts
