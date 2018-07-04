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

service rabbitmq-server restart
# make sure only 1 worker due to missing the synchronization between workers now
nohup celery -A ocata worker --concurrency=1 --loglevel=debug &

uwsgi --http :9006 --module ocata.wsgi --master --processes 4
