FROM python:2.7

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

EXPOSE 9006

WORKDIR /opt/ocata
RUN apt-get update && apt-get install -y memcached unzip rabbitmq-server
RUN wget -O /opt/multicloud-openstack-ocata.zip "https://nexus.onap.org/service/local/artifact/maven/redirect?r=snapshots&g=org.onap.multicloud.openstack&a=multicloud-openstack-ocata&e=zip&v=LATEST" && \
    unzip -q -o -B /opt/multicloud-openstack-ocata.zip -d /opt/ && \
    rm -f /opt/multicloud-openstack-ocata.zip
RUN mkdir -p /var/log/onap/multicloud/openstack/ocata/
#COPY ./ .
RUN pip install -r requirements.txt

CMD "/opt/ocata/run.sh"
