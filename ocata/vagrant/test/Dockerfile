FROM multicloud-ocata:latest

RUN apt-get update && \
     apt-get install -y vim
ADD extsys.py /opt/ocata/lib/newton/newton/pub/msapi/extsys.py
ADD run.sh /opt/ocata/run.sh
RUN chmod 755 /opt/ocata/run.sh
