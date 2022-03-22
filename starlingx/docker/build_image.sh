#!/bin/bash

# Copyright (c) 2019 Intel Corporation.
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

DIRNAME=`dirname $0`
DOCKER_BUILD_DIR=`cd $DIRNAME/; pwd`
echo "DOCKER_BUILD_DIR=${DOCKER_BUILD_DIR}"
cd ${DOCKER_BUILD_DIR}

BUILD_ARGS="--no-cache"
VERSION="1.5.8-SNAPSHOT"
STAGING="1.5.8-STAGING"
OS_VERSION="starlingx"
IMAGE_NAME="nexus3.onap.org:10003/onap/multicloud/openstack-${OS_VERSION}"

if [ $HTTP_PROXY ]; then
    BUILD_ARGS+=" --build-arg HTTP_PROXY=${HTTP_PROXY}"
fi
if [ $HTTPS_PROXY ]; then
    BUILD_ARGS+=" --build-arg HTTPS_PROXY=${HTTPS_PROXY}"
fi

function build_image {
    docker build ${BUILD_ARGS} -t ${IMAGE_NAME}:${VERSION} -t ${IMAGE_NAME}:latest -t ${IMAGE_NAME}:${STAGING} .
}

function push_image {
    docker push ${IMAGE_NAME}:${VERSION}
    docker push ${IMAGE_NAME}:latest
    docker push ${IMAGE_NAME}:${STAGING}
}

build_image
push_image
