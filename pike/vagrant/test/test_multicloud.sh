#!/bin/bash
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
    curl http://172.16.77.40:9006/api/multicloud-pike/v0/swagger.json && break
done

for i in `cat tests`
do
    bash ./$i
done
