# Copyright 2017-2018 Wind River Systems, Inc.
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

from titanium_cloud.extensions.views import extensions
from titanium_cloud.extensions.views import epacaps
from titanium_cloud.extensions.views import fcaps


urlpatterns = [
    url(r'^sions/?$', extensions.Extensions.as_view()),
    url(r'^sions/epa-caps/?$', epacaps.EpaCaps.as_view()),
    url(r'^sions/guest-monitor/(?P<vserverid>[0-9a-zA-Z_-]+)/?$', fcaps.GuestMonitor.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
