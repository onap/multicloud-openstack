#!/usr/bin/env bash

set -e

cd devstack
cp /vagrant/compute.conf local.conf
ip=$(ip a s eth1 | grep inet | grep -v inet6 | sed "s/.*inet //" | cut -f1 -d'/')
host=$(hostname)
sed -i -e "s/HOSTIP/$ip/" -e "s/HOSTNAME/$host/" local.conf
./stack.sh
