#!/bin/bash
# Copyright (c) 2018 Intel Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
