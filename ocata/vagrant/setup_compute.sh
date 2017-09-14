#!/usr/bin/env bash

set -e

cd devstack
cp /vagrant/compute.conf local.conf
ip=$(ip a s enp0s8 | grep inet | grep -v inet6 | sed "s/.*inet //" | cut -f1 -d'/')
host=$(hostname)
sed -i -e "s/HOSTIP/$ip/" -e "s/HOSTNAME/$host/" local.conf
./stack.sh

sudo apt-get update -y
sudo apt-get install -y putty
echo y | plink -ssh -l vagrant -pw vagrant 192.168.0.10 "bash /vagrant/setup_cell.sh"
