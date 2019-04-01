#!/bin/bash
# Copyright (c) 2019 Intel Corporation.
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

memcached -d -m 2048 -u root -c 1024 -p 11211 -P /tmp/memcached1.pid
export PYTHONPATH=lib/share
uwsgi --http :9009 --module starlingx.wsgi --master --processes 4

if [ ${SSL_ENABLED} = "true" ]; then
    nohup uwsgi --https :9009,starlingx/pub/ssl/cert/cert.crt,starlingx/pub/ssl/cert/cert.key --module starlingx.wsgi --master --processes 4 &

else
    nohup uwsgi --http :9009 --module starlingx.wsgi --master --processes 4 &

logDir="/var/log/onap/multicloud/openstack/starlingx"
if [ ! -x  $logDir  ]; then
       mkdir -p $logDir
fi
while [ ! -f $logDir/starlingx.log ]; do
    sleep 1
done

tail -F $logDir/starlingx.log
