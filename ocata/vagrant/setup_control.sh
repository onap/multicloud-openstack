#!/bin/bash

set -ex

cd /opt/stack/devstack
cp /vagrant/control.conf ./local.conf
su stack -c "./stack.sh"

sed -i "s/recursion no;/recursion yes;\n    forwarders { 8.8.8.8; 8.8.8.4; };/" \
    /etc/bind/named.conf.options
service bind9 restart
