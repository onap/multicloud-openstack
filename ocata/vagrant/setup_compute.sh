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

cd devstack
cp /vagrant/compute.conf local.conf
data_if=$(ifconfig | grep 192.168.* -B 1 | awk -F " " 'NR==1{print $1}')
ip=$(ip a s $data_if | grep inet | grep -v inet6 | sed "s/.*inet //" | cut -f1 -d'/')
host=$(hostname)
sed -i -e "s/HOSTIP/$ip/" -e "s/HOSTNAME/$host/" local.conf
./stack.sh

sudo apt-get update -y
sudo apt-get install -y putty
echo y | plink -ssh -l vagrant -pw vagrant 192.168.0.10 "bash /vagrant/setup_cell.sh"
