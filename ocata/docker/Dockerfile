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

EXPOSE 9004

# COPY ./ /opt/ocata/
RUN apt-get update && \
    apt-get install -y memcached && \
    apt-get install -y unzip && \
    cd /opt/ && \
    wget -O multicloud-openstack-ocata.zip "https://nexus.onap.org/service/local/artifact/maven/redirect?r=snapshots&g=org.onap.multicloud.openstack&a=multicloud-openstack-ocata&e=zip&v=LATEST" && \
    unzip -q -o -B multicloud-openstack-ocata.zip && \
    chmod +x /opt/ocata/*.sh && \
    rm -f multicloud-openstack-ocata.zip && \
    pip install -r /opt/ocata/requirements.txt

WORKDIR /opt/ocata
CMD /bin/sh -c /opt/ocata/run.sh