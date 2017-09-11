FROM python:2

ARG HTTP_PROXY=${HTTP_PROXY}
ARG HTTPS_PROXY=${HTTPS_PROXY}

ENV http_proxy $HTTP_PROXY
ENV https_proxy $HTTPS_PROXY

ENV MSB_ADDR "127.0.0.1"
ENV MSB_PORT "80"
ENV AAI_ADDR "aai.api.simpledemo.openecomp.org"
ENV AAI_PORT "8443"
ENV AAI_SCHEMA_VERSION "v11"
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
    rm -f multicloud-openstack-newton.zip && \
    pip install -r /opt/newton/requirements.txt

WORKDIR /opt/newton
CMD /bin/sh -c /opt/newton/run.sh
