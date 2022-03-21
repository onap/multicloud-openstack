# Copyright (c) 2017-2019 Wind River Systems, Inc.
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

# Micro service of MultiCloud plugin for Wind River Titanium Cloud.

### local test with docker-composer:

docker-compose -f docker-compose-fcaps.yml build

docker-compose -f docker-compose-fcaps.yml up -d

docker ps

### Test memcached
docker exec -it openstack_worker_1 sh

cat <<EOF>testmemcached.py
import memcache
mem = memcache.Client(['memcached:11211'], debug=1)
mem.set("testkey1","testvalue1")
value1 = mem.get("testkey1")
print("memcached is working" if value1=="testvalue1" else "memcached is not working")
EOF

python testmemcached.py

exit

docker-compose -f docker-compose-fcaps.yml down