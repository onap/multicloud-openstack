#!/usr/bin/env bash

set -e

cd devstack
cp /vagrant/control.conf  local.conf
./stack.sh
