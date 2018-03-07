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

This is the code base extracted from plugin service for newton. It consists of:

1, common utilities which is irrelevant of any SBI to openstack, just some wrapper for API interaction with other ONAP components

2, newton_base which is the translation of MultiCloud NBI to OpenStack Newton NBI.

Since from ONAP perspective, there are limited API requests to OpenStack, the variation between different OpenStack release could be minimal and even invisible. So the MultiCloud Plugin service for Ocata, Pike might also be able to reuse this newton_base library. With this approach we could minimize the effort to maintain MultiCloud Plugin services for various OpenStack releases

3, UT helper which simulates the VIM response whenever the requests are issued towards underly OpenStack Newton.

