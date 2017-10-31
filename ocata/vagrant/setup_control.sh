#!/bin/bash

set -ex

cd devstack
cp /vagrant/control.conf  local.conf
./stack.sh

sudo sed -i "s/recursion no;/recursion yes;\n    forwarders { 8.8.8.8; 8.8.8.4; };/" \
    /etc/bind/named.conf.options
sudo service bind9 restart
