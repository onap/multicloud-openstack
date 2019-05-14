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

FROM python:2-slim

ARG HTTP_PROXY=${HTTP_PROXY}
ARG HTTPS_PROXY=${HTTPS_PROXY}

ENV http_proxy $HTTP_PROXY
ENV https_proxy $HTTPS_PROXY

ENV MSB_ADDR "127.0.0.1"
ENV MSB_PORT "80"
ENV AAI_ADDR "aai.api.simpledemo.openecomp.org"
ENV AAI_PORT "8443"
ENV AAI_SERVICE_URL ""
ENV AAI_SCHEMA_VERSION "v13"
ENV AAI_USERNAME "AAI"
ENV AAI_PASSWORD "AAI"

EXPOSE 9007

RUN groupadd -r onap && useradd -r -g onap onap

RUN apt-get update && \
    apt-get install -y memcached wget unzip gcc libssl-dev && \
    cd /opt/ && \
    wget -O /opt/multicloud-openstack-pike.zip "https://nexus.onap.org/service/local/artifact/maven/redirect?r=snapshots&g=org.onap.multicloud.openstack&a=multicloud-openstack-pike&e=zip&v=1.3.3-SNAPSHOT" && \
    unzip -q -o -B /opt/multicloud-openstack-pike.zip -d /opt/ && \
    rm -f /opt/multicloud-openstack-pike.zip && \
    pip install -r /opt/pike/requirements.txt && \
    apt-get --purge remove -y wget unzip gcc libssl-dev && \
    mkdir -p /var/log/onap/multicloud/openstack/pike && \
    chown onap:onap /var/log/onap -R && \
    apt-get -y autoremove && \
    chown onap:onap /opt/pike -R

RUN mkdir -p /var/log/onap/multicloud/openstack/pike/

USER onap
WORKDIR /opt/pike
CMD /bin/sh -c "/opt/pike/run.sh"
