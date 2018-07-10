FROM python:2

ENV MSB_ADDR "127.0.0.1"
ENV MSB_PORT "80"
ENV AAI_ADDR "aai.api.simpledemo.openecomp.org"
ENV AAI_PORT "8443"
ENV AAI_SCHEMA_VERSION "v13"
ENV AAI_USERNAME "AAI"
ENV AAI_PASSWORD "AAI"

EXPOSE 9006

COPY multicloud-openstack-pike.zip /opt
RUN apt-get update && \
    apt-get install -y vim memcached unzip && \
    cd /opt/ && \
    unzip -q -o -B multicloud-openstack-pike.zip && \
    chmod +x /opt/pike/*.sh && \
    rm -f multicloud-openstack-pike.zip && \
    pip install -r /opt/pike/requirements.txt

ADD extsys.py /opt/pike/lib/share/common/msapi/extsys.py

WORKDIR /opt/pike
CMD /bin/sh -c /opt/pike/run.sh
