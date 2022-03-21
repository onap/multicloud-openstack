#!/bin/sh
# Copyright (c) 2017-2018 Wind River Systems, Inc.
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

# memcached should be provided as sidecar to avoid GPLv3 license issue
# memcached -d -m 2048 -c 1024 -p 11211 -P /tmp/memcached1.pid
export PYTHONPATH=lib/share

#nohup python manage.py runserver 0.0.0.0:9007 2>&1 &

if [ ${SSL_ENABLED} = "true" ]; then
    nohup uwsgi --https :9007,pike/pub/ssl/cert/cert.crt,pike/pub/ssl/cert/cert.key,HIGH --module pike.wsgi --master --enable-threads --processes 4 &

else
    nohup uwsgi --http :9007 --module pike.wsgi --master --enable-threads --processes 4 &
fi

logDir="/var/log/onap/multicloud/openstack/pike"
if [ ! -x  $logDir  ]; then
       mkdir -p $logDir
fi
while [ ! -f $logDir/pike.log ]; do
    sleep 1
done

tail -F $logDir/pike.log
