#!/bin/bash

set -ex

mkdir -p ~/.pip
cp /vagrant/pip.conf ~/.pip/
sudo cp /vagrant/pip.conf /etc/pip.conf
