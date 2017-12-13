#!/bin/bash

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
