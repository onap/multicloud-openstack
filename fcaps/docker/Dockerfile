FROM python:2-alpine

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

RUN addgroup -S onap && adduser -S -G onap onap
# COPY ./ /opt/fcaps/

RUN apk update && \
    apk add uwsgi memcached wget unzip gcc make libc-dev libffi-dev openssl-dev && \
    cd /opt/ && \
    wget -O multicloud-openstack-fcaps.zip "https://nexus.onap.org/service/local/artifact/maven/redirect?r=snapshots&g=org.onap.multicloud.openstack&a=multicloud-openstack-fcaps&e=zip&v=1.3.0-SNAPSHOT" && \
    unzip -q -o -B multicloud-openstack-fcaps.zip && \
    chmod +x /opt/fcaps/*.sh && \
    rm -f multicloud-openstack-fcaps.zip && \
    pip install -r /opt/fcaps/requirements.txt && \
    apk del -y wget unzip gcc make libc-dev libffi-dev openssl-dev && \
    mkdir -p /var/log/onap/multicloud/fcaps && \
    chown onap:onap /var/log/onap -R && \
    chown onap:onap /opt/fcaps -R

USER onap

WORKDIR /opt/fcaps
CMD /bin/sh -c /opt/fcaps/run.sh
