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

from pike.registration.views import registration
from newton_base.openoapi import tenants

urlpatterns = [
    url(r'^', include('pike.swagger.urls')),
    url(r'^', include('pike.samples.urls')),
    url(r'^api/multicloud-pike/v0/(?P<vimid>[0-9a-zA-Z_-]+)/registry$',
        registration.Registry.as_view()),
    url(r'^api/multicloud-pike/v0/(?P<vimid>[0-9a-zA-Z_-]+)/exten',
        include('pike.extensions.urls')),
    url(r'^api/multicloud-pike/v0/(?P<vimid>[0-9a-zA-Z_-]+)/',
             include('pike.proxy.urls')),

]


