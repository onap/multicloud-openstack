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

EXPOSE 9011

RUN groupadd -r onap && useradd -r -g onap onap
# COPY ./ /opt/fcaps/

RUN apt-get update && \
    apt-get install -y memcached wget unzip gcc && \
    apt-get install -y unzip && \
    cd /opt/ && \
    wget -O multicloud-openstack-fcaps.zip "https://nexus.onap.org/service/local/artifact/maven/redirect?r=snapshots&g=org.onap.multicloud.openstack&a=multicloud-openstack-fcaps&e=zip&v=1.3.0-SNAPSHOT" && \
    unzip -q -o -B multicloud-openstack-fcaps.zip && \
    chmod +x /opt/fcaps/*.sh && \
    rm -f multicloud-openstack-fcaps.zip && \
    pip install -r /opt/fcaps/requirements.txt && \
    apt-get --purge remove -y wget unzip gcc && \
    apt-get -y autoremove && \
    chown onap:onap /opt/fcaps -R

USER onap

WORKDIR /opt/fcaps
CMD /bin/sh -c /opt/fcaps/run.sh
