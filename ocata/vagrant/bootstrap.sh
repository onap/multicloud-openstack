#!/bin/bash

set -ex

if [[ $(whoami) != "root" ]]; then
    echo "Error: This script must be run as root!"
    exit 1
fi

apt-get update
useradd -s /bin/bash -d /opt/stack -m stack
echo "stack ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/stack
apt-get install -y git openvswitch-switch
git clone https://github.com/openstack-dev/devstack /opt/stack/devstack --branch stable/ocata
chown -R stack:stack /opt/stack/

ovs-vsctl add-br br-ex
ip=$(ip a s enp0s9 | grep inet | grep -v inet6 | sed "s/.*inet//" | cut -f2 -d' ')
ip address flush enp0s9
ovs-vsctl add-port br-ex enp0s9
ip a a $ip dev br-ex
ip link set dev br-ex up
ip link set dev enp0s9 up
