# Copyright (c) 2019 Intel Corporation.
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
from starlingx.registration.views import registration

urlpatterns = [
    url(r'^', include('starlingx.swagger.urls')),
    url(r'^', include('starlingx.samples.urls')),

    # API v0
    url(r'^api/multicloud-starlingx/v0/(?P<vimid>[0-9a-zA-Z_-]+)/registry/?$',
        registration.Registry.as_view()),
    url(r'^api/multicloud-starlingx/v0/(?P<vimid>[0-9a-zA-Z_-]+)/?$',
        registration.Registry.as_view()),
    url(r'^api/multicloud-starlingx/v0/(?P<vimid>[0-9a-zA-Z_-]+)/',
        include('starlingx.proxy.urls')),

    # API v1, depreciated due to MULTICLOUD-335
    url(r'^api/multicloud-starlingx/v1/(?P<cloud_owner>[0-9a-zA-Z_-]+)/(?P<cloud_region_id>[0-9a-zA-Z_-]+)/registry/?$',
        registration.APIv1Registry.as_view()),
    url(r'^api/multicloud-starlingx/v1/(?P<cloud_owner>[0-9a-zA-Z_-]+)/(?P<cloud_region_id>[0-9a-zA-Z_-]+)/?$',
        registration.APIv1Registry.as_view()),
    url(r'^api/multicloud-starlingx/v1/(?P<cloud_owner>[0-9a-zA-Z_-]+)/(?P<cloud_region_id>[0-9a-zA-Z_-]+)/',
        include('starlingx.proxy.urlsV1')),
]
