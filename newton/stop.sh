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

ps auxww | grep 'manage.py runserver 0.0.0.0:9003' | awk '{print $2}' | xargs kill -9
ps auxww | grep 'memcached -d -m 2048 -u root -c 1024 -p 11211 -P /tmp/memcached1.pid' | awk '{print $2}' | xargs kill -9
