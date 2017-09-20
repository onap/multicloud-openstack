# Copyright (c) 2017 Wind River Systems, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

from django.conf.urls import include, url

from titanium_cloud.registration.views import registration
from newton.requests.views import tenants

urlpatterns = [
    url(r'^', include('titanium_cloud.swagger.urls')),
    url(r'^', include('titanium_cloud.samples.urls')),
    url(r'^api/multicloud-titanium_cloud/v0/(?P<vimid>[0-9a-zA-Z_-]+)/registry/?$',
        registration.Registry.as_view()),
    url(r'^api/multicloud-titanium_cloud/v0/(?P<vimid>[0-9a-zA-Z_-]+)/?$',
        registration.Registry.as_view()),
    url(r'^api/multicloud-titanium_cloud/v0/(?P<vimid>[0-9a-zA-Z_-]+)/exten',
        include('titanium_cloud.extensions.urls')),
    url(r'^api/multicloud-titanium_cloud/v0/(?P<vimid>[0-9a-zA-Z_-]+)/',
             include('titanium_cloud.proxy.urls')),
    url(r'^api/multicloud-titanium_cloud/v0/(?P<vimid>[0-9a-zA-Z_-]+)/tenants/?$',
             tenants.Tenants.as_view()),
    url(r'^api/multicloud-titanium_cloud/v0/(?P<vimid>[0-9a-zA-Z_-]+)/'
        '(?P<tenantid>[0-9a-zA-Z_-]{8,})/', include('titanium_cloud.requests.urls')),
]


