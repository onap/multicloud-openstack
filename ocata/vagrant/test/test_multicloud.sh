#!/bin/bash
sudo apt-get update -y
sudo apt-get install -y docker.io 

git clone http://gerrit.onap.org/r/multicloud/openstack
cd openstack/ocata/docker
sudo docker build -t multicloud-ocata:latest .
cd /vagrant/test
sudo docker build -t multicloud-ocata-test:latest .
sudo docker network create --subnet=172.16.77.0/24 onap
sudo docker run -d -t  --name ocata-test --network onap --ip 172.16.77.40 -e MSB_ADDR=172.16.77.40 -e MSB_PORT=9004 multicloud-ocata-test

while true; do
    sleep 10
    curl http://172.16.77.40:9004/api/multicloud-ocata/v0/swagger.json && break
done

for i in `cat tests`
do
    bash ./$i
done
