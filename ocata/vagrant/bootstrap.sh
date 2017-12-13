#!/bin/bash

set -ex

sudo apt-get update -y
sudo apt-get install git -y
git clone https://github.com/openstack-dev/devstack
cd devstack; git checkout stable/ocata
sudo apt-get install openvswitch-switch -y
sudo ovs-vsctl add-br br-ex
ip=$(ip a s eth2 | grep inet | grep -v inet6 | sed "s/.*inet//" | cut -f2 -d' ')
sudo ip address flush eth2
sudo ovs-vsctl add-port br-ex eth2
sudo ip a a $ip dev br-ex
sudo ip link set dev br-ex up
sudo ip link set dev eth2 up
