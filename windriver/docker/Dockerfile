FROM python:2-slim

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

EXPOSE 9005

RUN groupadd -r onap && useradd -r -g onap onap
# COPY ./ /opt/windriver/

RUN apt-get update && \
    apt-get install -y memcached wget unzip gcc libssl-dev && \
    cd /opt/ && \
    wget -O multicloud-openstack-windriver.zip "https://nexus.onap.org/service/local/artifact/maven/redirect?r=snapshots&g=org.onap.multicloud.openstack&a=multicloud-openstack-windriver&e=zip&v=1.3.0-SNAPSHOT" && \
    unzip -q -o -B multicloud-openstack-windriver.zip && \
    chmod +x /opt/windriver/*.sh && \
    rm -f multicloud-openstack-windriver.zip && \
    pip install -r /opt/windriver/requirements.txt && \
    apt-get --purge remove -y wget unzip gcc libssl-dev && \
    apt-get -y autoremove && \
    mkdir -p /var/log/onap/multicloud/openstack/windriver && \
    chown onap:onap /var/log/onap -R && \
    chown onap:onap /opt/windriver -R

USER onap

WORKDIR /opt/windriver
CMD /bin/sh -c /opt/windriver/run.sh
