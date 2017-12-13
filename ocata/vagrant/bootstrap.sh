#!/bin/bash

set -ex

sudo apt-get update -y
sudo apt-get install git -y
git clone https://github.com/openstack-dev/devstack
cd devstack; git checkout stable/ocata
sudo apt-get install openvswitch-switch -y
sudo ovs-vsctl add-br br-ex
ctl_if=$(ifconfig | grep 192.168.* -B 1 | awk -F " " 'NR==4{print $1}')
ip=$(ip a s $ctl_if | grep inet | grep -v inet6 | sed "s/.*inet//" | cut -f2 -d' ')
sudo ip address flush $ctl_if
sudo ovs-vsctl add-port br-ex $ctl_if
sudo ip a a $ip dev br-ex
sudo ip link set dev br-ex up
sudo ip link set dev $ctl_if up
