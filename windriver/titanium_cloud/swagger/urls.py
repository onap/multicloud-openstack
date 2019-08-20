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

from titanium_cloud.swagger.views import SwaggerJsonViewDepreciated
from titanium_cloud.swagger.views import APIv1SwaggerJsonViewDepreciated
from titanium_cloud.swagger.views import SwaggerJsonView
from titanium_cloud.swagger.views import APIv1SwaggerJsonView

URLPATTERNS = [
    # API v0, depreciated
    url(r'^api/multicloud-titanium_cloud/v0/swagger.json$', SwaggerJsonViewDepreciated.as_view()),

    # API v1, depreciated
    url(r'^api/multicloud-titanium_cloud/v1/swagger.json$', APIv1SwaggerJsonViewDepreciated.as_view()),

    # API v0, new namespace: MULTICLOUD-335
    url(r'^api/multicloud-titaniumcloud/v0/swagger.json$', SwaggerJsonView.as_view()),

    # API v1, new namespace: MULTICLOUD-335
    url(r'^api/multicloud-titaniumcloud/v1/swagger.json$', APIv1SwaggerJsonView.as_view()),

]

urlpatterns = format_suffix_patterns(URLPATTERNS)
