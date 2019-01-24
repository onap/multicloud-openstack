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

from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from starlingx.swagger.views import SwaggerJsonView
from starlingx.swagger.views import APIv1SwaggerJsonView

urlpatterns = [
    url(r'^api/multicloud-starlingx/v0/swagger.json$', SwaggerJsonView.as_view()),
    url(r'^api/multicloud-starlingx/v1/swagger.json$', APIv1SwaggerJsonView.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
