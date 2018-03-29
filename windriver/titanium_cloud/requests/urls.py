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

from titanium_cloud.requests.views import imagefile

urlpatterns = [
    url(r'^networks(/(?P<networkid>[0-9a-zA-Z_-]+))?',
        network.Networks.as_view()),
    url(r'^subnets(/(?P<subnetid>[0-9a-zA-Z_-]+))?',
        subnet.Subnets.as_view()),
    url(r'^images(/(?P<imageid>[0-9a-zA-Z_-]+))?',
        image.Images.as_view()),
    # image-file
    url(r'^api/multicloud-titanium_cloud/v0/(?P<vimid>[0-9a-zA-Z_-]+)/image-file(/(?P<imageid>[0-9a-zA-Z_-]+))?',
        imagefile.ImageFile.as_view()),
    url(r'^volumes(/(?P<volumeid>[0-9a-zA-Z_-]+))?',
        volume.Volumes.as_view()),
    url(r'^servers(/(?P<serverid>[0-9a-zA-Z_-]+))?',
        server.Servers.as_view()),
    url(r'^ports(/(?P<portid>[0-9a-zA-Z_-]+))?',
        vport.Vports.as_view()),
    url(r'^flavors(/(?P<flavorid>[0-9a-zA-Z_-]+))?',
        flavor.Flavors.as_view()),
    url(r'^limits$', limits.Limits.as_view()),
    url(r'^hosts(/(?P<hostname>[0-9a-zA-Z_-]+))?', hosts.Hosts.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
