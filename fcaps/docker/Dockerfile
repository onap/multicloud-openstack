FROM python:3-alpine

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
COPY ./multicloud-openstack-fcaps-*.zip /opt/multicloud-openstack-fcaps.zip

RUN apk update && \
    apk add pcre pcre-dev uwsgi memcached wget unzip gcc make libc-dev libffi-dev openssl-dev && \
    cd /opt/ && \
    unzip -q -o -B multicloud-openstack-fcaps.zip && \
    chmod +x /opt/fcaps/*.sh && \
    rm -f multicloud-openstack-fcaps.zip && \
    pip3 install -r /opt/fcaps/requirements.txt && \
    pip3 install -r /opt/fcaps/uwsgi-requirements.txt && \
    apk del wget unzip gcc make libc-dev libffi-dev openssl-dev pcre-dev && \
    mkdir -p /var/log/onap/multicloud/fcaps && \
    chown onap:onap /var/log/onap -R && \
    chown onap:onap /opt/fcaps -R

USER onap

WORKDIR /opt/fcaps
CMD /bin/sh -c /opt/fcaps/run.sh
