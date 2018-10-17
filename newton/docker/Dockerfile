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

FROM python:2

ARG HTTP_PROXY=${HTTP_PROXY}
ARG HTTPS_PROXY=${HTTPS_PROXY}

ENV http_proxy $HTTP_PROXY
ENV https_proxy $HTTPS_PROXY

ENV MSB_ADDR "127.0.0.1"
ENV MSB_PORT "80"
ENV AAI_ADDR "aai.api.simpledemo.openecomp.org"
ENV AAI_PORT "8443"
ENV AAI_SCHEMA_VERSION "v13"
ENV AAI_USERNAME "AAI"
ENV AAI_PASSWORD "AAI"

EXPOSE 9003

# COPY ./ /opt/newton/
RUN apt-get update && \
    apt-get install -y memcached && \
    apt-get install -y unzip && \
    cd /opt/ && \
    wget -O multicloud-openstack-newton.zip "https://nexus.onap.org/service/local/artifact/maven/redirect?r=snapshots&g=org.onap.multicloud.openstack&a=multicloud-openstack-newton&e=zip&v=LATEST" && \
    unzip -q -o -B multicloud-openstack-newton.zip && \
    chmod +x /opt/newton/*.sh && \
    rm -f multicloud-openstack-newton.zip && \
    pip install -r /opt/newton/requirements.txt

WORKDIR /opt/newton
CMD /bin/sh -c /opt/newton/run.sh
