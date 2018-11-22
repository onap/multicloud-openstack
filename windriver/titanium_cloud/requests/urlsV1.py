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

from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from newton_base.openoapi import network
from newton_base.openoapi import subnet
from newton_base.openoapi import image
from newton_base.openoapi import volume
from newton_base.openoapi import server
from newton_base.openoapi import vport
from newton_base.openoapi import limits
from newton_base.openoapi import hosts
from newton_base.openoapi import flavor

urlpatterns = [
    url(r'^networks(/(?P<networkid>[0-9a-zA-Z_-]+))?',
        network.APIv1Networks.as_view()),
    url(r'^subnets(/(?P<subnetid>[0-9a-zA-Z_-]+))?',
        subnet.APIv1Subnets.as_view()),
    url(r'^images(/(?P<imageid>[0-9a-zA-Z_-]+))?',
        image.APIv1Images.as_view()),
    url(r'^volumes(/(?P<volumeid>[0-9a-zA-Z_-]+))?',
        volume.APIv1Volumes.as_view()),
    url(r'^servers(/(?P<serverid>[0-9a-zA-Z_-]+))/action/?$',
        server.ServerAction.as_view()),
    url(r'^servers(/(?P<serverid>[0-9a-zA-Z_-]+))?',
        server.APIv1Servers.as_view()),
    url(r'^ports(/(?P<portid>[0-9a-zA-Z_-]+))?',
        vport.APIv1Vports.as_view()),
    url(r'^flavors(/(?P<flavorid>[0-9a-zA-Z_-]+))?',
        flavor.APIv1Flavors.as_view()),
    url(r'^limits$', limits.APIv1Limits.as_view()),
    url(r'^hosts(/(?P<hostname>[0-9a-zA-Z_-]+))?', hosts.APIv1Hosts.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
