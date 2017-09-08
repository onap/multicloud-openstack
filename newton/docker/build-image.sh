#!/bin/bash

IMAGE="multicloud-openstack-newton"
VERSION="latest"

docker build -t ${IMAGE}:${VERSION} .
