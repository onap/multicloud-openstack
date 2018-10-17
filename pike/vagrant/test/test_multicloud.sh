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
sudo apt-get install -y docker.io maven npm virtualenv python-dev

git clone http://gerrit.onap.org/r/oparent
mkdir $HOME/.m2
cp oparent/settings.xml $HOME/.m2

git clone /openstack
cd openstack
mvn clean install
cp pike/target/multicloud-openstack-pike*.zip pike/vagrant/test/multicloud-openstack-pike.zip

cd pike/vagrant/test
sudo docker build -t multicloud-pike-test:latest .
sudo docker network create --subnet=172.16.77.0/24 onap
sudo docker run -d -t  --name pike-test --network onap --ip 172.16.77.40 -e MSB_ADDR=172.16.77.40 -e MSB_PORT=9007 multicloud-pike-test

while true; do
    sleep 10
    curl http://172.16.77.40:9007/api/multicloud-pike/v0/swagger.json && break
done

for i in `cat tests`
do
    bash ./$i
done
