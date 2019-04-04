#!/bin/bash
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

memcached -d -m 2048 -u root -c 1024 -p 11211 -P /tmp/memcached1.pid
export PYTHONPATH=lib/share


#nohup python manage.py runserver 0.0.0.0:9006 2>&1 &

if [ ${SSL_ENABLED} = "true" ]; then
    nohup uwsgi --https :9006,ocata/pub/ssl/cert/cert.crt,ocata/pub/ssl/cert/cert.key --module ocata.wsgi --master --enable-threads --processes 4 &

else
    nohup uwsgi --http :9006 --module ocata.wsgi --master --enable-threads --processes 4 &
fi

logDir="/var/log/onap/multicloud/openstack/ocata"
if [ ! -x  $logDir  ]; then
       mkdir -p $logDir
fi
while [ ! -f $logDir/ocata.log ]; do
    sleep 1
done

tail -F $logDir/ocata.log
