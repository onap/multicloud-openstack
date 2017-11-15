#!/bin/bash

ORG="onap"
VERSION="1.0.0-SNAPSHOT"
STAGING="1.0.0-STAGING"
PROJECT="multicloud"
IMAGE="openstack-newton"
IMAGE_NAME="${ORG}/${PROJECT}/${IMAGE}"

BUILD_ARGS="--no-cache"
if [ $HTTP_PROXY ]; then
    BUILD_ARGS+=" --build-arg HTTP_PROXY=${HTTP_PROXY}"
fi
if [ $HTTPS_PROXY ]; then
    BUILD_ARGS+=" --build-arg HTTPS_PROXY=${HTTPS_PROXY}"
fi

function usage {
    cat << EOF
Usage: build_image.sh [-p] [-?]
Optional arguments:
    -p
        Push docker images
EOF
}

function build_image {
    /opt/docker/docker-compose build
}

function push_image {
    local DOCKER_REPOSITORY="nexus3.onap.org:10003"
    docker tag ${IMAGE_NAME}:latest ${DOCKER_REPOSITORY}/${IMAGE_NAME}:latest
    docker push ${DOCKER_REPOSITORY}/${IMAGE_NAME}:latest

    docker tag ${DOCKER_REPOSITORY}/${IMAGE_NAME}:latest ${DOCKER_REPOSITORY}/${IMAGE_NAME}:${VERSION}
    docker push ${DOCKER_REPOSITORY}/${IMAGE_NAME}:${VERSION}

    docker tag ${DOCKER_REPOSITORY}/${IMAGE_NAME}:${VERSION} /${DOCKER_REPOSITORY}/${IMAGE_NAME}:${STAGING}
    docker push ${DOCKER_REPOSITORY}/${IMAGE_NAME}:${STAGING}
}

is_push_image="False"
while getopts "p:" OPTION "${@:2}"; do
    case "$OPTION" in
    p)
        is_push_image="True"
        ;;
    \?)
        usage
        exit 1
        ;;
    esac
done

build_image
if [ "$is_push_image" == "True" ] ; then
    push_image
fi
