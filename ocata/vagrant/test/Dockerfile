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

ENV MSB_ADDR "127.0.0.1"
ENV MSB_PORT "80"
ENV AAI_ADDR "aai.api.simpledemo.openecomp.org"
ENV AAI_PORT "8443"
ENV AAI_SCHEMA_VERSION "v13"
ENV AAI_USERNAME "AAI"
ENV AAI_PASSWORD "AAI"

EXPOSE 9006

COPY multicloud-openstack-ocata.zip /opt
RUN apt-get update && \
    apt-get install -y vim memcached unzip && \
    cd /opt/ && \
    unzip -q -o -B multicloud-openstack-ocata.zip && \
    chmod +x /opt/ocata/*.sh && \
    rm -f multicloud-openstack-ocata.zip && \
    pip install -r /opt/ocata/requirements.txt

ADD extsys.py /opt/ocata/lib/share/common/msapi/extsys.py

WORKDIR /opt/ocata
CMD /bin/sh -c /opt/ocata/run.sh
