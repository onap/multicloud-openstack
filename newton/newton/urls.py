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

from django.conf.urls import include, url

from newton.registration.views import registration
from newton_base.openoapi import tenants
from newton.resource.views import capacity

urlpatterns = [
    url(r'^', include('newton.swagger.urls')),
    url(r'^', include('newton.samples.urls')),
    url(r'^api/multicloud-newton/v0/(?P<vimid>[0-9a-zA-Z_-]+)/registry$',
        registration.Registry.as_view()),
    url(r'^api/multicloud-newton/v0/(?P<vimid>[0-9a-zA-Z_-]+)$',
        registration.Registry.as_view()),
    url(r'^api/multicloud-newton/v0/(?P<vimid>[0-9a-zA-Z_-]+)/exten',
        include('newton.extensions.urls')),
    url(r'^api/multicloud-newton/v0/(?P<vimid>[0-9a-zA-Z_-]+)/',
             include('newton.proxy.urls')),
    url(r'^api/multicloud-newton/v0/(?P<vimid>[0-9a-zA-Z_-]+)/tenants$',
             tenants.Tenants.as_view()),
    url(r'^api/multicloud-newton/v0/(?P<vimid>[0-9a-zA-Z_-]+)/'
        '(?P<tenantid>[0-9a-zA-Z_-]{20,})/', include('newton.requests.urls')),
    # CapacityCheck
    url(r'^api/multicloud-newton/v0/(?P<vimid>[0-9a-zA-Z_-]+)/capacity_check/?$',
        capacity.CapacityCheck.as_view()),
]


